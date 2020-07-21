import numpy as np
import pandas as pd

def onset_time(onsets, curr_time, max_time=1000):
    onset = onsets[onsets["ons"] < curr_time]
    onset = onset.sort_values("ons", ascending=False)
    if len(onset) > 0:
        _time = onset.iloc[0].ons
        return curr_time - _time
    return max_time

def stim_times(df, stimuli, curr_time):
    curr_cat = None
    first = None; last = None
    df.sort_values("ons", ascending=True, inplace=True)
    df = df[df["category"] != "keypress"]
    for i, row in df.iterrows():
        if row["ons"] > curr_time: break
        if row["category"] != stimuli:
            curr_cat = row["category"]
            continue
        if row["category"] != curr_cat: first = curr_time - row["ons"]
        last = curr_time - row["ons"]
        curr_cat = row["category"]
    return first, last

def keypress_times(df, button, curr_time):
    df.fillna(0, inplace=True)
    key_stim = pd.to_numeric(df["stimulus"], errors="coerce").fillna(0)
    keys = df[(
        (df["category"] == "keypress") &
        (key_stim.astype(int) == int(button))
    )]
    t = onset_time(keys, curr_time)
    return t

def last_onset(onset_csv, task, curr_time, max_time=1000):
    task_stimuli = {
        "gonogo":       ["Go", "NoGo"],
        "conscious":    ["Anger", "Disgust", "Fear", "Happy", "Neutral", "Sad"],
        "nonconscious": ["Anger", "Disgust", "Fear", "Happy", "Neutral", "Sad"],
        "wm":           ["Baseline", "Nontarget", "Target"], # FIXME: this was NonTarget before
        "emotion":      ["Fear", "Neut"],
        "gambling":     ["Win", "Loss"]
    }
    all_stimuli  = set(np.concatenate(list(task_stimuli.values())))
    onset_timing = {stimuli + tail: max_time for stimuli in all_stimuli for tail in ["_first", "_last"]}
    onset_timing["1"] = max_time
    onset_timing["6"] = max_time
    if task == "rest": return onset_timing
    onset_df = pd.read_csv(onset_csv)
    for button in ["1", "6"]:
        onset_timing[button] = keypress_times(onset_df, button, curr_time)

    for stimuli in task_stimuli[task]:
        first, last = stim_times(onset_df, stimuli, curr_time)
        if last:
            onset_timing[stimuli + "_first"] = first
            onset_timing[stimuli + "_last" ] = last
    return onset_timing

"""
Not used in gen_data
"""
# def most_recent_onset(df, onset_names, time):
#     df = df[df.ons < time]
#     most_recent = dict()
#     for name in onset_names:
#         tmp = df[df.onset == name]
#         recent_ons = tmp.tail(1)["ons"].values
#         if len(recent_ons) == 0:
#             most_recent[name] = time - 100 # Put the onset time to 100 seconds in the past
#         else:
#             most_recent[name] = recent_ons[0]
#     return most_recent
# 
# def recent_onsets(df, trigger_time):
#     onset_names = df.onset.unique()
#     time = trigger_time / 1000
#     recent_onset = most_recent_onset(df, onset_names, time)
#     onset_diff = {k: v - trigger_time/1000 for k, v in recent_onset.items()}
#     return onset_diff
# 
# def _format_onsets(onsets):
#     all_onsets = ["go", "nogo", "anger", "happy", "neutral", "fear", "disgust", "sad"]
#     for onset in all_onsets:
#         if onset not in onsets:
#             onsets[onset] = -100
#     return onsets
# 
