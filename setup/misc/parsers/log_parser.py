import os
import re
import ast
import pandas as pd
from collections import namedtuple, OrderedDict


script_dir = os.path.dirname(os.path.abspath(__file__))


# Using ordered dict to ensure keys are in a somewhat sensible order in the final dataframe
# We automatically fill in missing keys to make the code a bit simpler.
class OrderedDefaultDict(OrderedDict):
    def __missing__(self, key):
        self[key] = value = None
        return value


# HACK type is more specific than category, sorry for using words that are so similar
LogLine = namedtuple('LogLine', ['type', 'time', 'category', 'data', 'orig_msg'])


def _parse(filename):
    '''
    This method reads a log file and parses it into a list of LogLine. It's a bit of a
    trivial abstraction, but the hope is to avoid doing any kind of string parsing
    elsewhere, and centralize it here, so that other methods simply perform logic
    on parsed outputs.
    '''
    with open(filename, 'r') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

    parsed = []

    for line in lines:
        splitline = line.split('\t')
        if len(splitline) != 3:
            # We just skip these as they tend to be error messages.
            continue

        time, category, msg = splitline
        time = float(time)

        msg_type = None
        data = {}

        if msg.startswith('New trial'):
            msg_type = 'New trial'
            match = re.match(r'New trial \(rep=(\d+), index=(\d+)\): (.*)', msg)
            assert match, 'Error matching "New trial" log: {}'.format(msg)
            rep, index, trial_string = match.groups()

            try:
                trial_data = ast.literal_eval(trial_string)
            except:
                # This is needed for ENGAGE 2 and possibily all centers that use windows instead of UNIX-based systems
                # As an example, here is what the log file looks like instead
                # OrderedDict([(u'stimulus', u'images/1,4.png'), (u'category', u'Anger'), (u'emotion', u'images/1,4.png')])
                if trial_string.startswith("OrderedDict("):
                    formatted_trial_string = trial_string[len("OrderedDict("):-1]
                    pre_trial_data = ast.literal_eval(formatted_trial_string)
                    trial_data = dict()
                    for pair in pre_trial_data:
                        trial_data[pair[0]] = pair[1]

            data = OrderedDict(rep=int(rep), index=int(index), trial=trial_data)
        elif msg.startswith("Created outcomeText"):
            msg_type = "Outcome"
            assert "TextStim" in msg, "%s cannot be parsed for MID/SID" % str(line)
            outcome = msg.split("TextStim")[1]
            formatted_trial_string = outcome.replace(", win=Window(...)", "") # HACK
            formatted_trial_string = "dict" + formatted_trial_string
            array = list # another hack because this dict has things like "pos=array([ 0.,  0.])"
            data    =  eval(formatted_trial_string)
        elif ':' in msg:
            msg_type, msg_content = msg.split(': ', 1)
            draw_on = msg_content == 'autoDraw = True'
            draw_off = msg_content == 'autoDraw = False'
            if draw_on or draw_off:
                # If we are drawing on or off, then this is a stimulus presentation
                data = OrderedDict(stimulus=msg_type, autoDraw=draw_on)
                # We set the type to be something generic, not specific to the stimulus name
                msg_type = 'Stimulus'
                # Maybe split stimulus into special case where it is instrText, and then below add case like 'New Tria' where we append a new line?
            elif msg_type == 'Keypress':
                data = OrderedDict(key=msg_content)

        if msg != "window1: blendMode = 'avg'":
            parsed.append(LogLine(type=msg_type, time=time, category=category, data=data, orig_msg=msg))

    return parsed

def _ensure_distinct_trials(log_lines):
    '''
    This method takes a list of log lines and reorders them
    so that trials are non-overlapping. PsychoPy's log lines will have
    overlapping trials because the "New trial ..." log occurs before
    the stimulus for the next trial has appeared, so there is potential
    for prior stimuli Keypress or autoDraw events to appear after
    a "New trial ..." log.
    '''

    first_trial_stimulus = None
    trial_event = None
    result = []

    for log_line in log_lines:
        if log_line.type == 'New trial':
            assert trial_event is None, (
                'Found two "New trial" logs without a stimulus presentation. "{}" '
                'was detected as the primary stimulus. If this is not the primary '
                'stimulus, ensure there is a consistent stimulus name across all '
                'trials, even training trials.').format(first_trial_stimulus)
            trial_event = log_line
            continue
        elif log_line.type == 'Stimulus':
            # When we have had our first trial, but have not had a stimulus yet,
            # we record this stimulus type to understand how to rearrange logs
            if trial_event is not None and first_trial_stimulus is None and log_line.data['autoDraw']:
                first_trial_stimulus = log_line.data['stimulus']

            if first_trial_stimulus == log_line.data['stimulus'] and log_line.data['autoDraw']:
                result.append(trial_event)
                trial_event = None
                result.append(log_line)
                continue

        result.append(log_line)

    return result

def _seperate_by_trial(parsed):
    result = list()
    trial = list()
    start = False
    for line in parsed:
        if line.type == "New trial":
            start = True
            if trial:
                result.append(trial)
                trial = list()
        if start: trial.append(line)
    if trial: result.append(trial)
    return result

def _find_start_end(lines):
    # get last autoDraw = True
    start = max([
            line for line in lines if (
                line.data["autoDraw"])
            ], key=lambda x: x.time)

    # get next autoDraw = False
    end = min([
            line for line in lines if (
                not line.data["autoDraw"] and
                line.time > start.time)
            ], key=lambda x: x.time)
    return start, end

def _determine_onset(trial, stimuli):
    ### Find start and duration
    stimulus = [
            line for line in trial if (
                "stimulus" in line.data and
                 line.data["stimulus"] in stimuli
            )
    ]
    start, end = _find_start_end(stimulus)
    row = dict()
    row["ons"], row["dur"] = start.time, end.time - start.time

    ### Find stimulus
    start = [line for line in trial if line.type == "New trial"]
    assert len(start) == 1, "Expected exactly 1 start"
    start = start[0]

    # Append relevant info for both criteria
    row["stimulus"] = start.data["trial"]["stimulus"]
    row["category"] = start.data["trial"]["category"]
    return row

def find_time_zero(parsed, delay=6):
    """ 6s for singleband scans.  8.52s delay for multiband scans. """
    line = [line for line in parsed if line.type and line.type.startswith("Trigger Sent")]
    assert len(line) == 1, "Should find exactly one trigger sent"
    return line[0].time + delay

def generate_onsets(trials, task):
    if task == "gonogo":
        return generate_onsets_gonogo(trials)
    elif task in ["conscious", "nonconscious"]:
        return generate_onsets_faces(trials)
    elif task == "workingmemMB":
        return generate_onsets_wm(trials)
    raise Exception("No log parser for task %s" % task)

def _button_presses(trials):
    presses = list()
    for trial in trials:
        for line in trial:
            if line.type != "Keypress":
                continue
            if line.data["key"] in ["5", "s", "equal"]:
                continue
            else:
                presses.append({"ons": line.time, "stimulus": line.data["key"], "category": "keypress"})
    return presses

def generate_onsets_gonogo(trials):
    onsets = _button_presses(trials)
    for trial in trials:
        onsets.append( _determine_onset(trial, stimuli=["gng_image"]) )
    return pd.DataFrame( onsets )

def generate_onsets_faces(trials):
    onsets = _button_presses(trials)
    for trial in trials:
        onsets.append( _determine_onset(trial, stimuli=["emotion_image", "noncon_image"]) )
    return pd.DataFrame( onsets )

def generate_onsets_wm(trials):
    """ FIXME: add new_criteria """
    onsets = _button_presses(trials)
    for trial in trials:
        onsets.append( _determine_onset(trial, stimuli=["wm_image", "image_2"]) )
    return pd.DataFrame( onsets )


def log_parser(log_filepath, dst_path, task):
    parsed = _parse(log_filepath)
    parsed = _ensure_distinct_trials(parsed)
    trials = _seperate_by_trial(parsed)

    df = generate_onsets(trials, task)
    time_0 = find_time_zero(parsed)
    df["ons"] = df["ons"] - time_0
    df.sort_values("ons", inplace = True)
    df.to_csv(dst_path)


if __name__ == '__main__':
    ### Gather args
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('filepath', help='The path to the log file.', type=str)
    arg_parser.add_argument('dst', help='The path to the output directory.', type=str)
    arg_parser.add_argument('task', help='The task name for the log.', type=str)

    ### Parse args
    args = arg_parser.parse_args()
    log_filepath = args.filepath
    dst_path = args.dst
    task = args.task
    log_parser(log_filepath, dst_path, task)

