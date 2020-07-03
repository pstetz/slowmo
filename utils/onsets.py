import pandas as pd

ONSETS = [
        "Go", "Target", "Anger", "Disgust",
        "Neutral", "1", "Happy", "Baseline",
        "NoGo", "Sad", "6", "Fear", "NonTarget"
]


def _onset_time(onsets, curr_time, max_time=1000):
    onset = onsets[onsets["ons"] < curr_time]
    onset = onset.sort_values("ons", ascending=False)
    if len(onset) > 0:
        _time = onset.iloc[0].ons
        return curr_time - _time
    return max_time

def stim_times(df, stimuli, curr_time):
    stim = df[df.category == stimuli]
    return _onset_time(stim, curr_time)

def keypress_times(df, button, curr_time):
    df.fillna(0, inplace=True)
    key_stim = pd.to_numeric(df["stimulus"], errors="coerce").fillna(0)
    keys = df[(
        (df["category"] == "keypress") &
        (key_stim.astype(int) == int(button))
    )]
    t = _onset_time(keys, curr_time)
    return t

def last_onset(onset_df, task, curr_time, max_time=1000):
    task_stimuli = {
        "gonogo":       ["Go", "NoGo"],
        "conscious":    ["Anger", "Disgust", "Fear", "Happy", "Neutral", "Sad"],
        "nonconscious": ["Anger", "Disgust", "Fear", "Happy", "Neutral", "Sad"],
        "workingmemSB": ["Baseline", "NonTarget", "Target"],
        "workingmemMB": ["Baseline", "NonTarget", "Target"],
    }
    all_stimuli  = set(np.concatenate(list(task_stimuli.values())))
    all_stimuli.update(["1", "6"])
    onset_timing = {stimuli: max_time for stimuli in all_stimuli}
    for button in ["1", "6"]:
        onset_timing[button] = keypress_times(onset_df, button, curr_time)

    for stimuli in task_stimuli[task]:
        _time = stim_times(onset_df, stimuli, curr_time)
        if _time:
            onset_timing[stimuli] = _time
    df = pd.DataFrame(onset_timing, index=[1])
    return df
