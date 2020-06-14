"""
Imports
"""
import os
import random
import numpy as np
import pandas as pd

from glob import glob
from tqdm import tqdm
from os.path import isdir, isfile, join

from info.misc import INFO_ORDER

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
os.environ['KMP_DUPLICATE_LIB_OK']='True'


def fmriprep_cols():
    """
    Really trusting Chris here!  Don't want to use aCompCor because
    the data may be denoised already and the number of vectors varies
    https://neurostars.org/t/confounds-from-fmriprep-which-one-would-you-use-for-glm/326/2
    """
    cols = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z", "framewise_displacement"]

def mask_info(masks, fmri, grey, coord):
    x, y, z, t = coord
    info = _in_mask(masks, x, y, z)
    for timepoint, label in [(t-1, "prev"), (t+1, "next")]:
        info = {**info, **_mean_activation(masks, fmri, grey, timepoint, label)}
    info["x"] = x
    info["y"] = y
    info["z"] = z
    info["t"] = t
    return info

def _get(row, item):
    return row[item]

def fmri_path(root, row):
    project = _get(row, "project")
    subject = _get(row, "subject")
    time_session = _get(row, "time_session")
    task = _get(row, "task")
    return join(root, project, time_map(time_session), subject, task)


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
    for name in ["prev", "next", "gm", "wm", "csf", "info"]:
        np.save(join(input_folder, f"{name}.npy"), batch[name])
    np.save(join(input_folder, "pred.npy"), preds)

def load_row(row_path):
    fmri      = _get_data(join(row_path, "normalized.nii.gz"), is_fmri=True)
    onset_df  = pd.read_csv(join(row_path, "onsets.csv"))

    anat["gm"]  = _get_data(join(row_path, "..", "structural", "gm_probseg.nii.gz"))
    anat["wm"]  = _get_data(join(row_path, "..", "structural", "wm_probseg.nii.gz"))
    anat["csf"] = _get_data(join(row_path, "..", "structural", "csf_probseg.nii.gz"))
    return fmri, onset_df, anat

def _last_save(training_path):
    training = glob(join(training_path, "*"))
    if len(training) == 0:
        return 0
    i = max(training)
    i = os.path.basename(i)
    return int(i) + 1

ONSETS = [
        "Go", "Target", "Anger", "Disgust",
        "Neutral", "1", "Happy", "Baseline",
        "NoGo", "Sad", "6", "Fear", "NonTarget"
]

def setup_task_info():
    TR = _get(row, "TR")
    task = _get(row, "task")
    print(i, _get(row, "project"), _get(row, "subject"), _get(row, "task"))
    return task_info

def setup_info():
    info = pd.concat([pd.DataFrame(row[train_cols]).T] * batch_size).reset_index(drop=True)

def setup_voxels():
    """
    FIXME: need to sort also because so that way time can be saved by
    loading the fMRI in chunks
    """
    available_volumes = np.load("./available_volumes.npy")
    training_voxels = cartesian( available_volumes, np.array(range(2, fmri.shape[3]-2)) )
    training_index = random.sample(range(len(training_voxels)), batch_size*10)
    return training_voxels

def row_images(row):
    row_path = fmri_path(join(root, "raw"), row)
    return fmri, anat

def append_anat(anat, batch, x, y, z):
    for name in anat:
        batch[name].append(img_region(anat[name], x, y, z, r=RADIUS))

def append_func(fmri, batch, x, y, z, t):
    for name, timepoint in [("prev", t-1), ("next", t+1)]:
        batch[name].append(img_region(fmri[:, :, :, timpoint], x, y, z, r=RADIUS))

def append_masks():
    info["mask"].append
    mask_rows.append( mask_info(masks, fmri, grey, (x, y, z, t))  )

def combine_info(info):
    mask = pd.DataFrame(info["masks"])
    onsets = pd.DataFrame(info["onsets"])
    df = pd.concat(mask, onsets, ignore_index=True, axis=1) #FIXME: double check the shape
    for key, value in info["general"].items():
        df[key] = value
    return df[INFO_ORDER]

def checkpoint()
    info_df = combine_info(info)
    if not isdir(input_folder):
        os.makedirs(input_folder)
    batch["info"] = pd.concat([
        onsets, info, pd.DataFrame(mask_rows)
    ], axis=1)
    batch["prev"], batch["next"] = np.array(batch["prev"]), np.array(batch["next"])
    preds = np.array(bold_signal)
    _save(input_folder, batch, preds)

    bold_signal.clear(); mask_rows.clear(); onsets.clear()
    for name in batch:
        batch[name].clear()


def append_onsets()
    onsets.append(last_onset(onset_df, task, TR * t, max_time=1000))

def gen_data(df, train_cols, training_path, masks, root, batch_size=128):
    for i, row in df.iterrows():
        dst_group = join(train_path, "%04d" % i)
        if glob(join(dst_group, "*")): continue

        anat = load_anats()
        info = setup_info(row)
        fmri, anat = row_images(row)

        batch = {name: list() for name in ["prev", "next", "gm", "wm", "csf"]}
        bold_signal = list()

        training_voxels = setup_voxels()
        for j, voxel in tqdm(enumerate(training_voxels), total=len(training_voxels)):
            x, y, z, t = voxel
            dst_batch = join(dst_group, "%02d" % (j // batch_size))

            bold.append(fmri[x, y, z, t])
            append_anat(anat, batch, x, y, z)
            append_func(fmri, batch, x, y, z, t)
            append_mask(fmri, anat, info, x, y, z, t)
            append_onsets(fmri, info, t)

            if (j + 1) % batch_size == 0:
                checkpoint(info, batch, bold)


if __name__ == "__main__":
    root = "/Volumes/hd_4tb"
    assert os.path.isdir(root), "Connect external harddrive!  Cannot find %s" % root
    masks = load_masks( join(root, "masks", "plip") )

    df                = pd.read_csv(join(root, "project", "model_input.csv"))
    train_cols        = [c for c in df.columns if c.startswith("is_")] + ["age"]

    training_path = join(root, "results", "training")
    gen_data(df, train_cols, training_path, masks, root)

"""
gen_data
FIXME: find a way to speed up processing if the task has a lot of volumes
"""
    """
    -- Features
    info.npy # contains
        webneuro, redcap, some task info (sms, pe0/pe1, x, y, z, t, etc),
        onsets, and mask relevant information
        ** Looks like {"general": {...}. "onsets": [{...}, ...], "masks": [{...}, ...]
    gm.npy # grey matter image
    wm.npy # white matter image
    csf.npy # CSF image
    prev.npy # Previous fMRI data
    next.npy # Next fMRI data

    -- Target
    bold.npy # The voxel series to be predicted
    """
