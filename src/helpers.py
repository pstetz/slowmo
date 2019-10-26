import numpy as np
import pandas as pd
from tqdm import tqdm

def voxel_radius(radius):
    valid = list()
    for i in range(radius+1):
        for j in range(radius+1):
            for k in range(radius+1):
                if i == 0 and j == 0 and k == 0:
                    continue
                if i**2 + j**2 + k**2 > radius**2:
                    continue

                for parity in ([1, 1, 1], [-1, 1, 1], [1, -1, 1], [1, 1, -1],
                               [-1, -1, 1], [-1, 1, -1], [1, -1, -1], [-1, -1, -1]):
                    if ((i == 0 and parity[0] == -1) or
                        (j == 0 and parity[1] == -1) or
                        (k == 0 and parity[2] == -1)):
                        continue
                    valid.append({"x":  i * parity[0], "y":  j * parity[1], "z":  k * parity[2]})
    return valid

def _valid_patient(patient, dicom_path, button, logger):
    """ FIXME: finish me """
    valid = True
    if not patient:
        logger.log()
        valid = False
    if not dicom_path:
        logger.log()
        valid = False
    if not button:
        logger.log()
        valid = False
    return valid

def _train_task(project, task, onsets, data, patient, is_ascending):
    for num_volume in len(data.shape[-1]):
        df = _gen_data(project, task, onsets, volume, patient, is_ascending, num_volume)
        model.train(df)

def _volume_data(dicoms, x, y, z, t, direction, radius):
    row = dict()
    volume = dicoms.get_volume(t + direction)
    for coord in voxel_radius(radius):
        i, j, k  = coord["x"], coord["y"], coord["z"]
        loc      = "i%d_j%d_k%d_t%d" % (i, j, k, direction)
        row[loc] = volume[x+i, y+j ,z+k]
    return row

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

