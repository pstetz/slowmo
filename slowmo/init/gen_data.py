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

def meets_qa(task_dir, session, threshold=0.1):
    regressors = glob(join(task_dir, f"*{session}*confounds_regressors.tsv"))
    assert len(regressors) == 1, f"{len(regressors)}, {task_dir}"
    df = pd.read_csv(regressors.pop(), sep="\t")
    num_vols = df.shape[0]
    discarded = len([c for c in df.columns if "motion_outlier" in c])
    return discarded / num_vols <= threshold


def row_images(root, row):
    row_path = join(root, row["subject"], "func", row["task"])
    fmri     = get_data(join(row_path, row["filename"]))

    anat = dict()
    anat_dir = join(row_path, "..", "..", "anat")
    for name in ["gm", "wm", "csf"]:
        anat[name]  = get_data(join(anat_dir, "%s_probseg.nii.gz" % name))
    return fmri, anat

def setup_task_info():
    TR = _get(row, "TR")
    task = _get(row, "task")
    print(i, _get(row, "project"), _get(row, "subject"), _get(row, "task"))
    return task_info

def setup_info(row, session, task):
    info = dict()
    info["general"] = dict()
    info["mri"] = list(); info["onsets"] = list()
    for key, value in row.items()
        if key in ONSETS_ORDER.keys():
            info["general"][key] = value
    return info

def row_images(row):
    row_path = fmri_path(join(root, "raw"), row)
    return fmri, anat

def combine_info(info):
    mri    = pd.DataFrame(info["mri"])
    onsets = pd.DataFrame(info["onsets"])
    df = pd.concat(mask, onsets, ignore_index=True, axis=1) #FIXME: double check the shape
    for key, value in info["general"].items():
        df[key] = value
    return df[INFO_ORDER]

def gen_data(training_path, masks, root, batch_size=128):
    session = "ses-00" # FIXME: get ses-01 too
    df = pd.read_csv(root, "wn_redcap.csv")
    df = df[df["subject"] == subject]
    for row in df.iterrows():
        subject = basename(subject_path)
        for task in tasks:
            dst_group = join(train_path, f"{subject}_{session}_{task}")
            if glob(join(dst_group, "*")): continue

            info = setup_info(root, subject, session, task)
            fmri, anat = row_images(root, subject, session, task)

            batch = {name: list() for name in ["prev_1", "prev_2", "next_1", "next_2", "gm", "wm", "csf"]}
            bold_signal = list()

            training_voxels = setup_voxels()
            for j, voxel in tqdm(enumerate(training_voxels), total=len(training_voxels)):
                x, y, z, t = voxel
                append_voxel(fmri, anat, info, batch, x, y, z, t)

                if (j + 1) % batch_size == 0:
                    dst_batch = join(dst_group, "%02d" % (j // batch_size))
                    checkpoint(info, batch, bold)

tasks = {
    "gonogo-sb-pe0",
    "conscious-sb-pe0",
    "nonconscious-sb-pe0",
    "rest-mb-pe0",
    "rest-mb-pe1",
#    "wm-mb-pe0",
#    "wm-sb-pe0",
#    "gambling-mb-pe0",
#    "emotion-mb-pe0",
}

with open("../info/order.json", "r") as f:
    INFO_ORDER = json.load(f)

if __name__ == "__main__":
    root = "/Volumes/hd_4tb/slowmo/data"
    assert os.path.isdir(root), "Connect external harddrive!  Cannot find %s" % root
    masks = load_masks( join(root, "masks", "plip") )
    training_path = join(root, "results", "training")
    gen_data(training_path, masks, root)

"""
batch[name].append(
    np.stack((_load_volume(fmri, x, y, z, timepoint), grey_data), axis=3)
)
"""
