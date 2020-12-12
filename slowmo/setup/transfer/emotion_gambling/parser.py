import os
import numpy as np
import pandas as pd
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join


TASKS = [
    ("emotion", "emotion-mb-pe0"),
    ("guessing", "gambling-mb-pe0")
]
DUMMY_SCAN_SEC = 8.52

def find_start(df):
    return df["countdownStartTime"].max()

def emotion_onsets(df):
    rows = list()
    for i, row in df.iterrows():
        category = row["trialCondition"]
        if "shape" == category.lower():
            category = "Neut"
        elif "face" == category.lower():
            category = "Fear"
        rows.append({
            "category": category,
            "dur": row["trialEndTime"] - row["trialStartTime"],
            "ons": row["trialStartTime"],
            "stimulus": row["trialCondition"],
        })
        for key, key_ons in get_keys(row, "trialResp.keys", "trialResp.rt"):
            rows.append({
                "category": "keypress",
                "dur": np.nan,
                "ons": row["trialStartTime"] + key_ons,
                "stimulus": key,
            })
    return pd.DataFrame(rows).sort_values("ons")

def get_keys(row, resp_col, rt_col):
    key = row[resp_col]
    rt  = row[rt_col]
    if type(key) is float and np.isnan(key):
        return []
    elif ", " in str(key):
        keys = key[1:-1].split(", ")
        rts = rt[1:-1].split(", ")
        ret = list()
        for key, rt in zip(keys, rts):
            ret.append(({"2": 1, "3": 6}[key], float(rt)))
        return ret
    elif len(key) == 3:
        key = {"2": 1, "3": 6}[key[1]]
        return [(key, float(rt[1:-1]))]
    raise Exception(f"Improper value {key}")

def guessing_onsets(df):
    rows = list()
    for i, row in df.iterrows():
        category = row["trialCondition"]
        if "lose" in category.lower():
            category = "Loss"
        elif "win" in category.lower():
            category = "Win"
        rows.append({
            "category": category,
            "dur": row["feedbackEndTime"] - row["feedbackStartTime"],
            "ons": row["feedbackStartTime"],
            "stimulus": row["trialCondition"],
        })
        for key, key_ons in get_keys(row, "guessResp.keys", "guessResp.rt"):
            rows.append({
                "category": "keypress",
                "dur": np.nan,
                "ons": row["feedbackStartTime"] + key_ons,
                "stimulus": key,
            })
    return pd.DataFrame(rows).sort_values("ons")

def parse(logfile, dst, task):
    df = pd.read_csv(logfile)
    time_0 = find_start(df)
    diff = abs(time_0 - DUMMY_SCAN_SEC)
    if diff > 0.5:
        print("WARNING: Expected offset different by %.4f seconds for %s" % (diff, logfile))

    df = df[df["trialNum"] != 0] # Skip to stimuli

    ### Create onsets (task specific)
    if task == "emotion":
        onsets = emotion_onsets(df)
    elif task == "guessing":
        onsets = guessing_onsets(df)

    onsets["ons"] = onsets["ons"] - time_0 # subtract the start time
    if not isdir(dirname(dst)): os.makedirs(dirname(dst))
    onsets.to_csv(dst, index=False)

def main():
    folder = "/share/leanew1/PANLab_Datasets/CONNECTOME/button"
    dst_dir = "/oak/stanford/groups/leanew1/users/pstetz/.slowmo/onsets"
    for subject_path in tqdm(glob(join(folder, "*"))):
        subject = basename(subject_path).lower()

        for name, task in TASKS:
            dst = join(dst_dir, subject, task, "onsets.csv")
            if task == "guessing":
                dst = join(dst_dir, subject, "gambling", "onsets.csv")
            if isfile(dst): continue

            task_dir = join(subject_path, "s1", name)
            logfile = glob(join(task_dir, "*_wide.csv"))
            if len(logfile) > 1:
                print(f"{subject} {name}")
                continue
            if len(logfile) == 0: continue
            logfile = logfile.pop()
            print(dst)
            parse(logfile, dst, name)

if __name__ == "__main__":
    main()

