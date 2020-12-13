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
from slowmo.utils.mri import load_image, save_image, get_data, norm_image

def meets_qa(nifti_path, threshold=0.1):
    df = get_confounds(nifti_path)
    num_vols = df.shape[0]
    discarded = len([c for c in df.columns if "motion_outlier" in c])
    return discarded / num_vols <= threshold

def get_confounds(nifti_path):
    nifti_tail = "_space-MNI152NLin6Asym_desc-smoothAROMAnonaggr_bold.nii.gz"
    confounds_tail = "_desc-confounds_regressors.tsv"
    filename = basename(nifti_path).replace(nifti_tail, confounds_tail)
    filepath = join(dirname(nifti_path), filename)
    return pd.read_csv(filepath, sep="\t")

def fmriprep_cols(row, confound_df, t):
    """
    Really trusting Chris here!  Don't want to use aCompCor because
    the data may be denoised already and the number of vectors varies
    https://neurostars.org/t/confounds-from-fmriprep-which-one-would-you-use-for-glm/326/2
    """
    cols = ["trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z", "framewise_displacement"]
    for col in cols:
        row[col] = confound_df.loc[t, col]
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
    training_voxels.sort(key=lambda x: x[-1]) # sort by time
    return training_voxels

def mask_cache(masks, fmri, grey, t):
    if t not in MASK_CACHE:
        MASK_CACHE[t] = mri.mean_activation(masks, fmri, grey, t)
    return MASK_CACHE[t]

def mask_info(masks, fmri, grey, t):
    info = dict()
    for timepoint, label in [
            (t-1, "prev_1"), (t-2, "prev_2"),
            (t+1, "next_1"), (t+2, "next_2")
    ]:
        mask_values = mask_cache(masks, fmri, grey, timepoint)
        for mask in mask_values:
            info["%s_%s" % (mask, label)] = mask_values[mask]
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

def append_mri(confound_df, masks, fmri, anat, info, x, y, z, t):
    row = mask_info(masks, fmri, anat["gm"], t)
    for name, value in [("x", x), ("y", y), ("z", z), ("t", t)]:
        row[name] = value
    row = fmriprep_cols(row, confound_df, t)
    info["mri"].append(row)

def combine_info(info):
    mri    = pd.DataFrame(info["mri"])
    onsets = pd.DataFrame(info["onsets"])
    df = pd.concat([mri, onsets], axis=1) #FIXME: double check the shape
    for key, value in info["general"].items():
        df[key] = value
    order = [np.nan] * len(INFO_ORDER)
    for key, val in INFO_ORDER.items():
        order[val] = key
    return df[order]

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
    info["mri"].clear(); info["onsets"].clear(); bold.clear()

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
    for name in TASKS:
        name = name.split("-")[0]
        if name == "wm": name = "workingmemory"
        info["general"][f"is_{name}"] = int(name == task.split("-")[0])
    info["general"]["is_pe0"] = int(task.endswith("pe0"))
    info["general"]["is_mb"] = int(task.split("-")[1] == "mb")
    return info

def get_raw_func(task_path):
    if not meets_qa(task_path):
        return False

    # Normalizes the brain image
    mask = "/share/leanew1/pstetz/masks/MNI152_T1_2mm_brain_mask.nii"
    fmri   = load_image(task_path)
    data   = get_data(fmri)
    mask_data = get_data(mask)
    norm_data = norm_image(data, mask_data)
    tmp_path = join(TMP_DIR, basename(task_path))
    save_image(norm_data, tmp_path, affine=fmri.affine)
    norm_data = get_data(tmp_path)
    return norm_data

def resample(src, dst):
    from slowmo.utils.fsl_command import fsl_command
    reference = "/share/leanew1/pstetz/masks/MNI152_T1_2mm_brain_mask.nii"
    fsl_command("flirt", "-in", src, "-ref", reference, "-out", dst, "-applyxfm")

def get_raw_anat(subject_dir):
    # Need to resample data
    anat = dict()
    anat_dir = join(subject_dir, "anat")
    for name in ["gm", "wm", "csf"]:
        search = join(anat_dir, "*_space-MNI152NLin6Asym_label-%s_probseg.nii.gz" % name.upper())
        matches = glob(search)
        assert len(matches) < 2, "Duplicate structurals in %s" % matches
        assert len(matches) != 0, "No structurals in %s" % search
        filepath = matches.pop()
        tmp_filepath = join(TMP_DIR, basename(filepath))
        resample(filepath, tmp_filepath)
        anat[name] = mri.get_data(tmp_filepath)
    return anat

def row_images(subject_dir, task_path):
    fmri = get_raw_func(task_path)
    if fmri is False:
        return False, False

    anat = get_raw_anat(subject_dir)
    return fmri, anat

def load_masks(mask_dir):
    masks = glob(join(mask_dir, "*.nii"))
    masks = [{
        "code": basename(mask).split("_")[0],
        "data": nib.load(mask).get_fdata(),
    } for mask in masks]
    return masks

def bids_info(filepath, tag):
    filename = basename(filepath)
    info = [elem for elem in filename.split("_") if elem.startswith(tag)]
    assert len(info) == 1
    return info.pop().split("-")[1]

def get_avail_tasks(subject_dir):
    tasks = list()
    for session_path in glob(join(subject_dir, "ses-*")):
        session = basename(session_path)
        if session not in {"ses-00", "ses-01"}: continue # FIXME: hacky but only want baseline
        for task_path in glob(join(session_path, "func", "*-smoothAROMAnonaggr_bold.nii.gz")):
            task = bids_info(task_path, "task")
            acq = bids_info(task_path, "acq")
            pe = bids_info(task_path, "dir")
            taskname = f"{task}-{acq}-{pe}"
            if not taskname in TASKS: continue
            tasks.append((taskname, task_path))
    return tasks

def gen_data(src_dir, but_dir, dst_dir, df, masks, batch_size=128):
    # FIXME: make the batch_size way bigger for next round!
    for i, row in df.iterrows():
        subject = row["subject"].lower()
        bids_sub = "sub-" + subject.upper()
        subject_dir = join(src_dir, bids_sub)
        task_avail = get_avail_tasks(subject_dir)
        for task, task_path in task_avail:
            session = "ses-" + bids_info(task_path, "ses")
            TR = 0.71 if task.split("-")[1] == "mb" else 2
            dst_group = join(dst_dir, f"{subject}_{session}_{task}")
            if glob(join(dst_group, "*")): continue
            onset_csv = join(but_dir, subject, task, "onsets.csv")
            if not task.startswith("rest") and not isfile(onset_csv): continue
            fmri, anat = row_images(subject_dir, task_path)
            if fmri is False or anat is False: continue
            confound_df = get_confounds(task_path)
            print(dst_group)

            info = setup_info(row, task)
            batch = {name: list() for name in ["prev_1", "prev_2", "next_1", "next_2", "gm", "wm", "csf"]}
            bold = list()

            training_voxels = setup_voxels(fmri.shape[-1], batch_size)
            for j, voxel in tqdm(enumerate(training_voxels), total=len(training_voxels)):

                x, y, z, t = voxel
                bold.append(fmri[x, y, z, t])

                append_mri(confound_df, masks, fmri, anat, info, x, y, z, t)
                append_onsets(info, onset_csv, task, TR, t)
                append_anat(anat, batch, x, y, z)
                append_func(fmri, batch, x, y, z, t)

                if (j + 1) % batch_size == 0:
                    dst_batch = join(dst_group, "%02d" % (j // batch_size))
                    checkpoint(info, batch, bold, dst_batch)
            MASK_CACHE.clear()
        [os.remove(f) for f in glob(TMP_DIR + "/*.nii.gz")]

TASKS = {
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
TMP_DIR = "/scratch/pstetz/.slow"
MASK_CACHE = dict()

if __name__ == "__main__":
    src_dir = "/oak/stanford/groups/leanew1/ramirezc/hcpdes_latest/derivatives/functional_derivatives/fmriprep"
    dst_dir = "/oak/stanford/groups/leanew1/users/pstetz/.slowmo/training"
    but_dir = "/oak/stanford/groups/leanew1/users/pstetz/.slowmo/onsets"
    wn_path = "/oak/stanford/groups/leanew1/users/pstetz/.slowmo/wn_redcap.csv"
    df = pd.read_csv(wn_path)
    masks = load_masks( "/scratch/pstetz/.slow/masks" )
    gen_data(src_dir, but_dir, dst_dir, df, masks)

