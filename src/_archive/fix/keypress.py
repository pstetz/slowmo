"""
The keypress onsets were not recorded properly for a large amount of training inputs

This script goes through
"""

import os
import numpy as np
import pandas as pd
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, join

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
        _fix_file(f, raw_path, TR=TR)

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
    onset_csv = join(raw_path, "onsets.csv")
    onsets = pd.read_csv(onset_csv)
    data = np.load(filepath, allow_pickle=True)
    times = data[:, t_index]
    for button, index in [("1", 11), ("6", 12)]:
        press = [_keypress_times(onsets, button, t * TR) for t in times]
        data[:, index] = press
    np.save(filepath, data)

def _onset_time(onsets, curr_time):
    onset = onsets[onsets["ons"] < curr_time]
    onset = onset.sort_values("ons", ascending=False)
    if len(onset) > 0:
        _time = onset.iloc[0].ons
        return curr_time - _time
    return False

def _keypress_times(df, button, curr_time):
    df.fillna(0, inplace=True)
    keys = df[(
        (df["category"] == "keypress") &
        (df["stimulus"].astype(int) == int(button))
    )]
    return _onset_time(keys, curr_time)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if len(args) == 0:
        root = "/Volumes/hd_4tb/results/cp_training"
    else:
        root = args.pop()
    assert len(args) == 0, "inappropriate arguments %s" % " ".join(sys.argv)
    keypress_fix(root)

