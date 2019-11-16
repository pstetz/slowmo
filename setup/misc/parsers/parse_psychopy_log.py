from __future__ import print_function
import pandas as pd
import ast
import re
from collections import namedtuple, OrderedDict
import os
import numpy as np


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


def convert_to_timing_file(filename):
    parsed = _parse(filename)
    parsed = _ensure_distinct_trials(parsed)

    trial_data_keys = None
    first_trial_stimulus = None

    result = [OrderedDefaultDict()]
    for log_line in parsed:
        if log_line.type == 'New trial':
            result.append(OrderedDefaultDict())

            trial_data = log_line.data['trial']
            if trial_data_keys is None:
                trial_data_keys = trial_data.keys()
            else:
                if set(trial_data.keys()) != set(trial_data_keys):
                    print(
                        (
                            'Warning: Found a discrepancy between trial keys for (rep={}, index={}). ' +
                            'Expected {} but found {}.'
                        ).format(
                            log_line.data['rep'], log_line.data['index'],
                            trial_data_keys, trial_data.keys()
                        )
                    )

            result[-1]['rep'] = log_line.data['rep']
            result[-1]['index'] = log_line.data['index']
            for key, value in trial_data.iteritems():
                result[-1]['trial.{}'.format(key)] = value
        elif log_line.type == 'Keypress':
            keyname = 'key.' + log_line.data['key']
            if keyname in result[-1]:
                print('Warning: Overwriting keypress {} with duplicate value {}'.format(
                    result[-1][keyname],
                    log_line.data[keyname],
                ))
            result[-1][keyname+'.time'] = log_line.time
            if first_trial_stimulus is not None:
                stimulus_presentation = result[-1]['stimulus.{}.on'.format(first_trial_stimulus)]
                result[-1][keyname+'.rt'] = log_line.time - stimulus_presentation
        elif log_line.type == 'Stimulus':
            # When we have had our first trial, but have not had a stimulus yet,
            # we record this stimulus type and use it to break up rows in the future.
            if trial_data_keys is not None and first_trial_stimulus is None and log_line.data['autoDraw']:
                first_trial_stimulus = log_line.data['stimulus']

            on_key = 'stimulus.{}.on'.format(log_line.data['stimulus'])
            off_key = 'stimulus.{}.off'.format(log_line.data['stimulus'])
            if log_line.data['autoDraw']:
                result[-1][on_key] = log_line.time
            else:
                result[-1][off_key] = log_line.time

    # HACK finding nicely ordered cols
    colsdict = OrderedDict()
    for r in result:
        for k in r.keys():
            colsdict[k] = True
            # We make sure to add in the .off version of a key when we
            # see the .on key.
            if k.endswith('.on'):
                colsdict[re.sub(r'.on$', '.off', k)] = True
    ordering = dict(rep=0, index=1, stimulus=2, key=3, trial=4)
    cols = colsdict.keys()
    cols.sort(key=lambda k: ordering[k.split('.')[0]])
    # HACK finding nicely ordered cols
    df = pd.DataFrame.from_records(result, columns=cols)
    return df


def _debug_timing(df):
    stim_cols = [
        c
        for c in df.columns
        # We want to make sure the column appears more than twice to avoid instructions
        # We choose 2 instead of 1 because some tasks have a training phase and then a test phase
        if df[c].notnull().sum() > 2
        # Should start with stimulus
        if c.startswith('stimulus.')
    ]

    def _disp(diff):
        return '{:.01f}ms'.format(diff * 1000)

    def _stim_log_name(col_a, col_b, overlapping_trials=False):
        col_a_bits = col_a.split('.')
        col_b_bits = col_b.split('.')
        if overlapping_trials:
            return '{}->next({})'.format(col_a_bits[1], col_b_bits[1])
        elif col_a_bits[1] == col_b_bits[1]:
            return col_a_bits[1]
        else:
            return '{}->{}'.format(col_a_bits[1], col_b_bits[1])

    for idx, (_, row) in enumerate(df.iterrows()):
        if idx == 0:
            # We skip first row since it is instruction text
            # HACK make this more robust
            continue
        total = 0
        print('index={}'.format(row['index']), end=' ')
        for col_a, col_b in zip(stim_cols[:-1], stim_cols[1:]):
            total += row[col_b] - row[col_a]
            print('{}={}'.format(_stim_log_name(col_a, col_b), _disp(row[col_b] - row[col_a])), end=' ')
        if idx != df.shape[0] - 1:
            col_a = stim_cols[-1]
            col_b = stim_cols[0]
            next_row = df.iloc[idx + 1]
            total += next_row[col_b] - row[col_a]
            print('{}={}'.format(
                _stim_log_name(col_a, col_b, overlapping_trials=True),
                _disp(next_row[col_b] - row[col_a])), end=' ')
        print('total={}'.format(_disp(total)))


task_to_stim_order = {
    1: pd.read_csv(os.path.join(script_dir, 'psychopy/GoNoGo-task/stimulus_order.csv')),
    3: pd.read_csv(os.path.join(script_dir, 'psychopy/EmotionConscious-task/stimulus_order.csv')),
    5: pd.read_csv(os.path.join(script_dir, 'psychopy/EmotionNonconscious-task/stimulus_order.csv')),
}



def generate_onsets(orig_df, task_number, output_dir):
    if task_number == 26:
        # This version of working memory is multiplex
        DUMMY_SCAN_SECONDS = 8.52
    else:
        # We have 3 dummy scans with TR=2s, so our dummy scan in seconds in 6s
        DUMMY_SCAN_SECONDS = 6
    stim_order = task_to_stim_order[task_number]

    # We look for the start of the task, which depends on the task type as some have training stimuli
    rep_starts, = np.where((orig_df['rep'] == 0) & (orig_df['index'] == 0))
    if task_number == 1:
        assert len(rep_starts) == 2, 'We expect two rep=0, index=0 trials for GNG, but found {}: {}'.format(len(rep_starts), rep_starts)
        start_index = rep_starts[1]
    else:
        assert len(rep_starts) == 1, 'We expect one rep=0, index=0 trials for most tasks.'
        start_index = rep_starts[0]

    # After s is pressed, we start the scanner, which takes ~0.5s because we sleep 0.5s when waiting for a connection.
    # HACK when possible, this should prefer our official "scan start" event
    scan_start = orig_df['key.s.time'][start_index - 1] + 0.5

    # We have training for some tasks and some header events for others. This line removes training and ensures we
    # start at the first stimulus. We copy to avoid issues with setting properties on views of a df.
    df = orig_df.iloc[start_index:].copy()

    # Then we compute .ons column
    if task_number == 1:
        stim_key = 'stimulus.gng_image.on'
        stim_order_key = 'stimulus'
    elif task_number == 3:
        stim_key = 'stimulus.emotion_image.on'
        stim_order_key = 'emotion'
    elif task_number in (4, 26):
        stim_key = 'stimulus.wm_image.on'
        stim_order_key = 'stimulus'
    elif task_number == 5:
        stim_key = 'stimulus.noncon_image.on'
        stim_order_key = 'noncon'

    # Ensure the stimulus ordering is the same as what was specified in the stimulus order CSV
    len_log_events = len(df['trial.{}'.format(stim_order_key)])
    assert len_log_events <= len(stim_order[stim_order_key]), \
        'Found more events in log than expected.'
    if len(stim_order[stim_order_key]) != len_log_events:
        # If we have too few items in our log, we should warn and truncate our list of expected stimuli
        print('Warning: Found {} items in log but expected {}. Truncating list of expected stimuli.'.format(
            len_log_events, len(stim_order[stim_order_key])))
        stim_order = stim_order.iloc[:len_log_events]
    assert np.all(stim_order[stim_order_key].values == df['trial.{}'.format(stim_order_key)].values), \
        'Found different stimulus filenames in stimulus ordering vs log'

    # For fMRI analysis, we are interested in the offset of a stimulus relative to the first
    # non-dummy TR of our fMRI scan. Since we discard 3 dummy scans with a TR of 2 seconds,
    # we should offset our scan start timing by 6 seconds and compute our simulus relative
    # to this offset scan start.
    df['ons'] = df[stim_key] - scan_start - DUMMY_SCAN_SECONDS
    df['num'] = df['index'] + 1
    # We pull in category from the stimulus order CSV
    df['category'] = stim_order.category.values

    # We warn when the actual offset seems like it might be wrong.
    if task_number == 1:
        expected_offset = 1.5
    elif task_number == 4:
        expected_offset = 4
    elif task_number == 26:
        expected_offset = 1.48
    elif task_number in (3, 5):
        expected_offset = 2
    actual_offset = df.iloc[0]['ons']
    if abs(actual_offset - expected_offset) > 0.025:
        print(
            'Warning: First stimulus offset from beginning of non-dummy scan data should '
            'have been {} but was {}'.format(expected_offset, actual_offset))

    # We appropriately offset our df here so that we can simply write all remaining events
    if task_number in (3, 5):
        # Out of a spirit of neuroticism, we ensure that our block design aligns correctly with our expectations
        checking_category = None
        for _, row in df.iterrows():
            if row['index'] % 8 == 0:
                checking_category = row.category
            else:
                assert row.category == checking_category, 'Expected to find category {} but found {}'.format(
                    checking_category, row.category)

        # Since blocks are every 8, we simply take the first of the block for its offset and category
        df = df.iloc[::8]

    # We write them to a file based on name of category.
    for category, group in df.groupby('category'):
        if category is None:
            continue
        result = group[['num', 'ons']].copy()
        result['num'] = result['num'].astype(np.int)
        result.to_csv(os.path.join(output_dir, '{}_Onsets.csv'.format(category)), index=False)


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('filename', help='The path to the log file.', type=str)
    arg_parser.add_argument('--task_number', help='The task number for the log.', type=int)
    arg_parser.add_argument('--debug_timing', help='Log debug information regarding task timing.', action='store_true')
    args = arg_parser.parse_args()

    filename = args.filename
    task_num = args.task_number
    df = convert_to_timing_file(filename)

    if task_num is None:
        new_filename = os.path.splitext(os.path.basename(filename))[0] + '.parsed-log.csv'
        df.to_csv(os.path.join(os.path.dirname(filename), new_filename), index=False)
    else:
        output_dir = os.path.dirname(filename)
        generate_onsets(df, task_num, output_dir)

    if args.debug_timing:
        _debug_timing(df)
