"""
Imports
"""
import os
import json
import random
import numpy as np
import pandas as pd
import nibabel as nib

from glob import glob
from tqdm import tqdm
from os.path import abspath, basename, dirname, isdir, isfile, join

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
os.environ['KMP_DUPLICATE_LIB_OK']='True'

import slowmo.utils.mri as mri
from slowmo.utils.onsets import last_onset

def meets_qa(task_dir, session, threshold=0.1):
    regressors = glob(join(task_dir, f"*{session}*confounds_regressors.tsv"))
    assert len(regressors) == 1, f"{len(regressors)}, {task_dir}"
    df = pd.read_csv(regressors.pop(), sep="\t")
    num_vols = df.shape[0]
    discarded = len([c for c in df.columns if "motion_outlier" in c])
    return discarded / num_vols <= threshold

def fmriprep_cols(row, task_dir, session, t):
    """
    Really trusting Chris here!  Don't want to use aCompCor because
    the data may be denoised already and the number of vectors varies
    https://neurostars.org/t/confounds-from-fmriprep-which-one-would-you-use-for-glm/326/2
    """
    cols = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z", "framewise_displacement"]
    filepath = glob(join(task_dir, f"*{session}_*-confounds_regressors.tsv")).pop()
    df = pd.read_csv(filepath, sep="\t")
    for col in cols:
        row[col] = df.loc[t, col]
    return row

def setup_voxels(dim4, batch_size, skip=2):
    # FIXME: need to sort also because so that way time can be saved by loading the fMRI in chunks
    filepath = join(dirname(abspath(__file__)), "../info/available_volumes.npy")
    available_volumes = np.load(filepath)
    training_voxels = mri.cartesian(
        available_volumes,
        np.array(range(skip, dim4-skip))
    )
    training_index = random.sample(range(len(training_voxels)), batch_size*10)
    training_voxels = [training_voxels[i] for i in training_index]
    return training_voxels

def mask_info(masks, fmri, grey, coord):
    x, y, z, t = coord
    info = mri.in_mask(masks, x, y, z)
    for timepoint, label in [
            (t-1, "prev_1"), (t-2, "prev_2"),
            (t+1, "next_1"), (t+2, "next_2")
    ]:
        info = {**info, **mri.mean_activation(masks, fmri, grey, timepoint, label)}
    info["x"] = x
    info["y"] = y
    info["z"] = z
    info["t"] = t
    return info

def append_anat(anat, batch, x, y, z):
    for name in anat:
        batch[name].append(mri.nii_region(anat[name], x, y, z, r=RADIUS))

def append_func(fmri, batch, x, y, z, t):
    for name, timepoint in [
            ("prev_1", t-1), ("prev_2", t-2),
            ("next_1", t+1), ("next_2", t+2)
            ]:
        batch[name].append(mri.nii_region(fmri[:, :, :, timepoint], x, y, z, r=RADIUS))

def append_mri(task_dir, session, masks, fmri, anat, info, x, y, z, t):
    row = mask_info(masks, fmri, anat["gm"], (x, y, z, t))
    for name, value in [("x", x), ("y", y), ("z", z), ("t", t)]:
        row[name] = value
    row = fmriprep_cols(row, task_dir, session, t)
    info["mri"].append(row)

def combine_info(info):
    mri    = pd.DataFrame(info["mri"])
    onsets = pd.DataFrame(info["onsets"])
    df = pd.concat([mri, onsets], ignore_index=True, axis=0) #FIXME: double check the shape
    for key, value in info["general"].items():
        df[key] = value
    return df[INFO_ORDER.keys()]

def checkpoint(info, batch, bold, dst_dir):
    if not isdir(dst_dir):
        os.makedirs(dst_dir)
    info_df = combine_info(info)
    for name in batch:
        arr = np.array(batch[name])
        np.save(join(dst_dir, f"{name}.npy"), arr)
        batch[name].clear()

    np.save(join(dst_dir, "bold.npy"), np.array(bold))
    info_df.to_csv(join(dst_dir, "info.csv"), index=False)
    info["mri"].clear(); info["onsets"].clear()
    bold.clear(); mask_rows.clear(); onsets.clear()

def append_onsets(info, onset_csv, task, TR, t):
    task = task.split("-")[0]
    info["onsets"].append(
        last_onset(onset_csv, task, TR * t, max_time=1000)
    )

def last_save(training_path):
    training = glob(join(training_path, "*"))
    if len(training) == 0:
        return 0
    i = max(training)
    i = os.path.basename(i)
    return int(i) + 1

def setup_info(row, task):
    info = dict()
    info["general"] = dict()
    info["mri"] = list(); info["onsets"] = list()
    for key, value in row.items():
        if key in INFO_ORDER.keys():
            info["general"][key] = value
    for name in tasks:
        name = name.split("-")[0]
        if name == "wm": name = "workingmemory"
        info["general"][f"is_{name}"] = int(name == task.split("-")[0])
    info["general"]["is_pe0"] = int(task.endswith("pe0"))
    info["general"]["is_mb"] = int(task.split("-")[1] == "mb")
    return info

def row_images(subject_dir, session, task):
    task_dir = join(subject_dir, "func", task)
    if not isdir(task_dir): return False, False
    filepath = glob(join(task_dir, f"{session}_*_standardized.nii.gz"))
    if len(filepath) == 0:
        return False, False
    if not meets_qa(task_dir, session):
        return False, False
    fmri     = mri.get_data(filepath.pop())

    anat = dict()
    anat_dir = join(subject_dir, "anat")
    for name in ["gm", "wm", "csf"]:
        anat[name] = mri.get_data(join(anat_dir, "%s_probseg_resampled.nii.gz" % name))
    return fmri, anat

def load_masks(mask_dir):
    masks = glob(join(mask_dir, "*"))
    masks = [{
        "code": basename(mask).split("_")[0],
        "data": nib.load(mask).get_fdata(),
    } for mask in masks]
    return masks

def gen_data(training_path, masks, root, batch_size=12):
    session = "ses-00" # FIXME: get ses-01 too
    df = pd.read_csv(join(root, "wn_redcap.csv"))
    for i, row in df.iterrows():
        subject = row["subject"].lower()
        subject_dir = join(root, "fmri", "connectome", subject)
        for task in tasks:
            TR = 0.71 if task.split("-")[1] == "mb" else 2
            task_dir = join(subject_dir, "func", task)
            if task in {"wm-mb-pe0", "wm-sb-pe0", "gambling-mb-pe0", "emotion-mb-pe0"}: continue # FIXME: get rid of this
            fmri, anat = row_images(subject_dir, session, task)
            if fmri is False or anat is False: continue
            onset_csv = join(task_dir, "onsets.csv")
            if not task.startswith("rest") and not isfile(onset_csv): continue
            dst_group = join(training_path, f"{subject}_{session}_{task}")
            if glob(join(dst_group, "*")): continue
            print(subject, session, task)

            info = setup_info(row, task)

            batch = {name: list() for name in ["prev_1", "prev_2", "next_1", "next_2", "gm", "wm", "csf"]}
            bold = list()

            training_voxels = setup_voxels(fmri.shape[-1], batch_size)
            for j, voxel in tqdm(enumerate(training_voxels), total=len(training_voxels)):
                x, y, z, t = voxel
                bold.append(fmri[x, y, z, t])

                append_mri(task_dir, session, masks, fmri, anat, info, x, y, z, t)
                append_onsets(info, onset_csv, task, TR, t)
                append_anat(anat, batch, x, y, z)
                append_func(fmri, batch, x, y, z, t)

                if (j + 1) % batch_size == 0:
                    dst_dir = join(dst_group, "%02d" % (j // batch_size))
                    checkpoint(info, batch, bold, dst_dir)

tasks = {
    "gonogo-sb-pe0",
    "conscious-sb-pe0",
    "nonconscious-sb-pe0",
    "rest-mb-pe0",
    "rest-mb-pe1",
    "wm-mb-pe0",
    "wm-sb-pe0",
    "gambling-mb-pe0",
    "emotion-mb-pe0",
}

with open(join(dirname(abspath(__file__)), "../info/order.json"), "r") as f:
    INFO_ORDER = json.load(f)

RADIUS = 4

if __name__ == "__main__":
    root = "/Volumes/hd_4tb/slowmo/data"
    assert os.path.isdir(root), "Connect external harddrive!  Cannot find %s" % root
    masks = load_masks( join(root, "masks", "plip") )
    training_path = join(root, "results", "training")
    gen_data(training_path, masks, root)

