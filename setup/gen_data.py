"""
Imports
"""
import os
import random
import numpy as np
import pandas as pd
import nibabel as nib

from glob import glob
from tqdm import tqdm
from os.path import isdir, isfile, join

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
os.environ['KMP_DUPLICATE_LIB_OK']='True'

VOL_SKIP = 300 # Note: modifications in the script are needed besides this


"""
Masks
"""
def _load_masks(mask_dir):
    masks = glob(join(mask_dir, "*"))
    masks = [{
        "code": os.path.basename(mask).split("_")[0],
        "data": nib.load(mask).get_data(),
    } for mask in masks]
    return masks

def _in_mask(masks, x, y, z):
    result = dict()
    for mask in masks:
        code = mask["code"]
        data = mask["data"]
        result["in_%s" % code] = int(bool(data[x, y, z]))
    return result

def _mean_activation(masks, fmri, grey, t, label):
    activations = dict()
    for mask in masks:
        code, data = mask["code"], mask["data"]
        region = np.multiply(data, fmri[:, :, :, t])
        activations["mean_%s_%s" % (code, label)] = np.mean( np.multiply(grey, region) )
    return activations

def _mask_info(masks, fmri, grey, coord):
    x, y, z, t = coord
    info = _in_mask(masks, x, y, z)
    for timepoint, label in [(t-1, "prev"), (t+1, "next")]:
        info = {**info, **_mean_activation(masks, fmri, grey, timepoint, label)}
    info["x"] = x
    info["y"] = y
    info["z"] = z
    info["t"] = t
    return info


"""
fMRI
"""
def _load_volume(fmri, x, y, z, t):
    volume = nii_input(fmri[:, :, :, t], x, y, z)
    return np.array(volume)

def _load(filepath):
    return nib.as_closest_canonical(nib.load(filepath))

def _get_data(filepath, is_fmri=False):
    image = _load(filepath)
    data  = image.get_data()
    if is_fmri:
        #data  = data[:, :, :, VOL_SKIP:VOL_SKIP+151]
        pass
    return data

def _time_map(session):
    _map = {
        "s1": "000", "s2": "2MO", "s3": "6MO", "s4": "12MO", "s5": "24MO"
    }
    return _map[session]

def _get(row, item):
    return row[item]

def _fmri_path(row):
    _input = "/Volumes/hd_4tb/raw"
    project = _get(row, "project")
    subject = _get(row, "subject")
    time_session = _get(row, "time_session")
    task = _get(row, "task")
    return join(_input, project, _time_map(time_session), subject, task)

def nii_input(data, x, y, z, r = 4):
    return data[
        x - r : x + r + 1,
        y - r : y + r + 1,
        z - r : z + r + 1
    ]

"""
Onsets
"""
def _onset_time(onsets, curr_time):
    onset = onsets[onsets["ons"] < curr_time]
    onset = onset.sort_values("ons", ascending=False)
    if len(onset) > 0:
        _time = onset.iloc[0].ons
        return curr_time - _time
    return False

def _stim_time(df, stimuli, curr_time):
    stim = df[df.category == stimuli]
    return _onset_time(stim, curr_time)

def _keypress_times(df, button, curr_time):
    df.fillna(0, inplace=True)
    key_stim = pd.to_numeric(df["stimulus"], errors="coerce").fillna(0)
    keys = df[(
        (df["category"] == "keypress") &
        (key_stim.astype(int) == int(button))
    )]
    return _onset_time(keys, curr_time)

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
        onset_timing[button] = _keypress_times(onset_df, button, curr_time)

    for stimuli in task_stimuli[task]:
        _time = _stim_time(onset_df, stimuli, curr_time)
        if _time:
            onset_timing[stimuli] = _time
    df = pd.DataFrame(onset_timing, index=[1])
    return df


"""
Helpers
"""
def cartesian(data, timepoints):
    ret = list()
    for x, y, z in data:
        for t in timepoints:
            ret.append((x, y, z, t))
    return ret

def _save(input_folder, batch, preds):
    np.save(join(input_folder, "prev.npy"), batch["prev"])
    np.save(join(input_folder, "next.npy"), batch["next"])
    np.save(join(input_folder, "info.npy"), batch["info"])
    np.save(join(input_folder, "pred.npy"), preds)

def _load_row(row_path):
    fmri      = _get_data(join(row_path, "normalized.nii.gz"), is_fmri=True)
    grey      = _get_data(join(row_path, "..", "structural", "gm_probseg.nii.gz"))
    onset_df  = pd.read_csv(join(row_path, "onsets.csv"))
    return fmri, grey, onset_df

def _last_save(training_path):
    training = glob(join(training_path, "*"))
    if len(training) == 0:
        return 0
    i = max(training)
    i = os.path.basename(i)
    return int(i) + 1

"""
Main function
"""
def gen_data(df, train_cols, available_volumes, training_path, masks, batch_size=128):
    for i, row in df.iterrows():
        if glob(join(training_path, "%04d/*" % i)): continue
        TR = 2 if _get(row, "is_mb") == 0 else 0.71
        task = _get(row, "task")
        if task == "workingmemMB": continue

        print(i, _get(row, "project"), _get(row, "subject"), _get(row, "time_session"), _get(row, "task"))
        row_path = _fmri_path(row)
        fmri, grey, onset_df = _load_row(row_path)

        info = pd.concat([pd.DataFrame(row[train_cols]).T] * batch_size).reset_index(drop=True)

        batch = {"prev": list(), "next": list()}
        bold_signal, mask_rows, onsets = list(), list(), list()
        training_voxels = cartesian( available_volumes, np.array(range(1, fmri.shape[3]-1)) )
        training_index = random.sample(range(len(training_voxels)), batch_size*10)

        for j, index in tqdm(enumerate(training_index), total=batch_size*10):
            x, y, z, t = training_voxels[index]
            onsets.append(last_onset(onset_df, task, TR * t, max_time=1000))

            mask_rows.append( _mask_info(masks, fmri, grey, (x, y, z, t))  )
            grey_data = nii_input(grey, x, y, z)
            for name, timepoint in [("prev", t-1), ("next", t+1)]:
                batch[name].append(
                    np.stack((_load_volume(fmri, x, y, z, timepoint), grey_data), axis=3)
                )
            bold_signal.append(fmri[x, y, z, t])

            ### Fit to data
            if (j + 1) % batch_size == 0:
                input_folder = join(training_path, "%04d/%02d" % (i, j // batch_size))
                if not os.path.isdir(input_folder):
                    os.makedirs(input_folder)
                batch["info"] = pd.concat([
                    onsets, info, pd.DataFrame(mask_rows)
                ], axis=1)
                batch["prev"], batch["next"] = np.array(batch["prev"]), np.array(batch["next"])
                preds = np.array(bold_signal)
                _save(input_folder, batch, preds)
                batch = {"prev": list(), "next": list()}
                bold_signal, mask_rows, onsets = list(), list(), list()


if __name__ == "__main__":
    root = "/Volumes/hd_4tb"
    assert os.path.isdir(root), "Connect external harddrive!  Cannot find %s" % root
    masks = _load_masks( join(root, "masks", "plip") )

    df                = pd.read_csv(join(root, "project", "model_input.csv"))
    available_volumes = np.load("./available_volumes.npy")
    train_cols        = [c for c in df.columns if c.startswith("is_")] + ["age"]

    training_path = join(root, "results", "training")
    gen_data(df, train_cols, available_volumes, training_path, masks)

