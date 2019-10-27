import numpy as np
import pandas as pd
from tqdm import tqdm

def _gen_avail_volumes(shape, radius):
    x_min, x_max = radius, shape[0] - radius
    y_min, y_max = radius, shape[1] - radius
    z_min, z_max = radius, shape[2] - radius
    return np.array([(x, y, z) for x in range(x_min, x_max)
                      for y in range(y_min, y_max)
                      for z in range(z_min, z_max)
           ])

def _add_map(data, _map):
    for key in _map:
        _add_value(data, key, _map[key])

def _add_value(data, key, value):
    if not key in data:
        data[key] = list()
    data[key].append(value)

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

def _convert_float64_to_float32(df):
    for col in tqdm(df.columns):
        if df[col].dtype == np.float64:
            df[col] = df[col].astype(np.float32)
    return df

