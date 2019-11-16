"""
Unused
"""

"""
### MID
Main function that generates the onsets for the MID/SID given a button logfile.

As Christina explains here:
"so for the MID, there are (1) Win $5 anticipation, (2) Win $0 anticipation, (3) Lose $5 anticipation,
(4) Lose $0 anticipation, (5) Win $5 consumption, (6) Win $0 consumption, (7) Lose $5 consumption, and
(8) Lose $0 consumption.  where the anticipation phase is the onset and duration of cross 1 and
the consumption phase is the onset and duration of cross 3"


### Working memory
There are two different ways of parsing the WM task.
One with the intended instructions and one with the actual instructions
"""
def _wm_criteria_2(orig_df):
    """
    Look at the assigned category instead
    """
    prev = orig_df.stimulus
    curr = np.roll(prev, 1)

    df = orig_df.copy()
    df.loc[prev == curr, "category"] = "Target"
    df.loc[np.logical_and(prev != curr, df.category != "Baseline"), "category"] = "NonTarget"
    return df

def generate_onsets_mid(trials, output_dir, filename):
    onsets = list()
    for trial in trials:
        con_ons, con_dur, con_result = _determine_onset(trial, is_consumption=True)
        ant_ons, ant_dur, ant_result = _determine_onset(trial, is_consumption=False)
        onsets.append({"ons": con_ons, "dur": con_dur, "type": "%s_consumption" % con_result})
        onsets.append({"ons": ant_ons, "dur": ant_dur, "type": "%s_anticipation" % ant_result})
    return pd.DataFrame(onsets)

def _determine_onset_mid(trial, is_consumption=True):
    stimulus = {True: "cross_3", False: "cross_1"}[is_consumption]
    cross_lines = [line for line in trial if "stimulus" in line.data and line.data["stimulus"] == stimulus]

    start, end = _find_start_end(cross_lines)
    ons, dur = start.time, end.time - start.time

    ### Find start
    start = [line for line in trial if line.type == "New trial"]
    assert len(start) == 1, "Expected exactly 1 start"
    # outcome_map = {
    #         "-$0.00": "lose_0", "+$0.00": "win_0",
    #         "-$5.00": "lose_5", "+$5.00": "win_5"
    # }
    outcome_map = {
            "images/sqr.bmp": "lose_0", "images/cir.bmp": "win_0",
            "images/sqr3.bmp": "lose_5", "images/cir3.bmp": "win_5"
    }
    result = outcome_map[start[0].data["trial"]["stimulus"]]

    return ons, dur, result
