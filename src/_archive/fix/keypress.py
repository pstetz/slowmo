"""
The keypress onsets were not recorded properly for a large amount of training inputs

This script goes through
"""

import os
import numpy as np
import pandas as pd
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isfile, join

def keypress_fix(root):
    df = pd.read_csv(join(root, "..", "model_input.csv"))
    files = glob(join(root, "*", "*", "info.npy"))

    for f in tqdm(files):
        i = int(basename(dirname(dirname(f))))
        project, subject, time_session, task = _sample_info(df, i)
        raw_path = join("/Volumes/hd_4tb/raw", project, time_session, subject, task)
        TR = 2
        if task == "workingmemMB":
            TR = 0.71
        try:
            _fix_file(f, raw_path, TR=TR)
        except Exception as e:
            print(e)
            print(f)

def _time_map():
    _map = {
        "s1": "000",
        "s2": "2MO",
        "s3": "6MO",
        "s4": "12MO",
        "s5": "24MO",
    }
    return _map

def _sample_info(df, i):
    project = df.loc[i, "project"]
    subject = df.loc[i, "subject"]
    time_session = df.loc[i, "time_session"]
    task         = df.loc[i, "task"]
    time_session = _time_map()[time_session]
    return project, subject, time_session, task

def _fix_file(filepath, raw_path, TR=2, t_index=126):
    new_path = join(dirname(filepath), "fix_" + basename(filepath))
    if isfile(new_path):
        return
    onset_csv = join(raw_path, "onsets.csv")
    onsets = pd.read_csv(onset_csv)
    data = np.load(filepath, allow_pickle=True)
    times = data[:, t_index]
    for button, index in [("1", 5), ("6", 10)]:
        press = [_keypress_times(onsets, button, t * TR) for t in times]
        data[:, index] = press
    for stimuli, index in [
            ("Go",        0),
            ("Target",    1),
            ("Anger",     2),
            ("Disgust",   3),
            ("Neutral",   4),
            ("Happy",     6),
            ("Baseline",  7),
            ("NoGo",      8),
            ("Sad",       9),
            ("Fear",      11),
            ("NonTarget", 12),
    ]:
        press = [_stim_times(onsets, stimuli, t * TR) for t in times]
        data[:, index] = press
    np.save(new_path, data)

def _onset_time(onsets, curr_time, max_time=1000):
    onset = onsets[onsets["ons"] < curr_time]
    onset = onset.sort_values("ons", ascending=False)
    if len(onset) > 0:
        _time = onset.iloc[0].ons
        return curr_time - _time
    return max_time

def _keypress_times(df, button, curr_time):
    df.fillna(0, inplace=True)
    key_stim = pd.to_numeric(df["stimulus"], errors="coerce").fillna(0)
    keys = df[(
        (df["category"] == "keypress") &
        (key_stim.astype(int) == int(button))
    )]
    t = _onset_time(keys, curr_time)
    return t

def _stim_times(df, stimuli, curr_time):
    stim = df[df.category == stimuli]
    return _onset_time(stim, curr_time)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if len(args) == 0:
        root = "/Volumes/hd_4tb/results/training"
    else:
        root = args.pop()
    assert len(args) == 0, "inappropriate arguments %s" % " ".join(sys.argv)
    keypress_fix(root)

