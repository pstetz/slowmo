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

def most_recent_onset(df, onset_names, time):
    df = df[df.ons < time]
    most_recent = dict()
    for name in onset_names:
        tmp = df[df.onset == name]
        recent_ons = tmp.tail(1)["ons"].values
        if len(recent_ons) == 0:
            most_recent[name] = time - 100 # Put the onset time to 100 seconds in the past
        else:
            most_recent[name] = recent_ons[0]
    return most_recent

def recent_onsets(df, trigger_time):
    onset_names = df.onset.unique()
    time = trigger_time / 1000
    recent_onset = most_recent_onset(df, onset_names, time)
    onset_diff = {k: v - trigger_time/1000 for k, v in recent_onset.items()}
    return onset_diff

def _format_onsets(onsets):
    all_onsets = ["go", "nogo", "anger", "happy", "neutral", "fear", "disgust", "sad"]
    for onset in all_onsets:
        if onset not in onsets:
            onsets[onset] = -100
    return onsets
