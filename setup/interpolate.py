import ast
import json
import pickle
import numpy as np
import pandas as pd
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join
from gen_data import *

root = "/Users/pstetz/Desktop/confidential/.project"

# model = keras.models.load_model("/Volumes/hd_4tb/results/runs/run_2/2_nonlinear.h5")
model_path = join(root, "run/lgbm/3_full_data.pkl")
with open(model_path, "rb") as f:
    model = pickle.load(f)

with open(join(root, "summary/norm.json"), "r") as f:
    norm_info = json.load(f)

with open(join(root, "summary/info_order.json"), "r") as f:
    order = json.load(f)

norm_info = {order[k]: v for k, v in norm_info.items()}


def _grey_mean_std(stats_file):
    with open(stats_file, "r") as f:
        data = json.load(f)
        data = ast.literal_eval(data)
        data = ast.literal_eval(data)
    means, stds = [], []
    for k, v in data.items():
        means.append(v["mean"])
        stds.append(v["std"])
    mn = sum(means) / len(means)
    std = (sum([e**2 for e in stds]) / len(means)) ** 0.5
    return mn, std

df = pd.read_csv(join(root, "summary/model_input.csv"))
onset_df = pd.read_csv(join(root, "interpolate/raw/conn152/gonogo/onsets.csv"))
gvol = nib.load(join(root, "interpolate/raw/conn152/structural/gm_probseg.nii.gz")).get_fdata()
grey_mean, grey_std = _grey_mean_std(join(root, "summary/grey_norm.json"))
gvol[:, :, :] = np.divide(np.subtract(gvol[:, :, :], grey_mean), grey_std)

mask_dir = join(root, "masks")
masks = load_masks(mask_dir)
train_cols = [c for c in df.columns if c.startswith("is_")] + ["age"]

def _inbetween_file(path1, path2):
    """
    z --> indicates half step forwards
    a --> indicates half step back
    s --> indicates a stop
    """
    name1, name2 = basename(path1), basename(path2)
    directory = dirname(path1)
    if not name1.endswith("s.npy") and not name2.endswith("s.npy"):
        return join(directory, name1.replace(".npy", "_zs.npy"))
    elif len(name1) > len(name2):
        return join(directory, name1.replace("s.npy", "zs.npy"))
    return join(directory, name2.replace("s.npy", "as.npy"))

def _get_time(path, TR=2):
    name = basename(path).replace("s.npy", "").replace(".npy", "")
    if "_" not in name:
        return TR * int(name)
    _time = int(name.split("_")[0]) * TR
    for i, c in name.split("_")[1]:
        if c == "a":
            _time -= 1 / 2**(i+1)
        elif c == "z":
            _time += 1 / 2**(i+1)
        else: raise
    return _time

def norm_features(x, norm_info):
    for feat in x.columns:
        mn = norm_info[feat]["mean"]
        std = norm_info[feat]["std"]
        x[feat] = np.divide(np.subtract(x[feat], mn), std)
    return x

def mean_activation(masks, pvol, nvol, gvol):
    activations = dict()
    for label, volume in [("prev", pvol), ("next", nvol)]:
        for mask in masks:
            code, data = mask["code"], mask["data"]
            region = np.multiply(data, volume)
            activations["mean_%s_%s" % (code, label)] = np.mean( np.multiply(gvol, region) )
    return activations

def at_most_level(num, filepath):
    name = basename(filepath)
    t = int(name.split(".")[0].split("_")[0])
    if t > 20:
        return False
    if "_" not in name:
        return 0 <= num
    return len(name.split("_")[1].replace("s.npy", "")) <= num

def guess_volume(
        pvol, nvol, gvol, t_index, stable_x,
        model, masks, norm_info,
    ):
    mask = nib.load(join(root, "interpolate/MNI152_T1_2mm_brain_mask.nii.gz")).get_fdata()
    volume = np.zeros(shape=pvol.shape)
    x_n, y_n, z_n = volume.shape
    stable_x = stable_x.append([stable_x] * (z_n - 1), ignore_index=True)
    for i in tqdm(range(x_n)):
        for j in range(y_n):
            x = stable_x.copy()
            x["x"], x["y"], x["t"] = i, j, t_index
            x["z"] = list(range(z_n)) # FIXME: double check that this is correct for z
            for m in masks:
                x["in_%s" % m["code"]] = [int(bool(m["data"][i, j, k])) for k in range(z_n)]
            norm_x = norm_features(x, norm_info)
            for label, data in [("prev", pvol), ("next", nvol), ("grey", gvol)]:
                norm_x[label] = data[i, j, :]
            volume[i, j, :] = model.predict(norm_x)
    return np.multiply(volume, mask)

volume_dir = join(root, "interpolate/volumes")

record = 291 # CONN152 gonogo
TR = 2 # seconds
subject_df = pd.DataFrame(df.iloc[record][train_cols]).T.reset_index(drop=True)

for lvl in range(6):
    print("Interpolating on a %.2f second interval" % (TR / (2 ** (lvl + 1))))
    files = list(sorted(glob(join(volume_dir, "*"))))
    files = [f for f in files if at_most_level(lvl, f)]
    for i in range(len(files) - 1):
        file1, file2 = files[i], files[i + 1]
        dst = _inbetween_file(file1, file2)
        if isfile(dst):
            print("%s already exists.  Skipping" % dst)
            continue
        print("Interpolating between files \n\t%s\n\t%s \n\nto create\n\t%s" % (file1, file2, dst))
        print("")
        pvol = np.load(file1)
        nvol = np.load(file2)
        t = (_get_time(file1, TR=TR) + _get_time(file2, TR=TR)) / 2

        onsets = last_onset(onset_df, "gonogo", t).reset_index(drop=True)
        mask_activations = mean_activation(masks, pvol, nvol, gvol)
        stable_x = pd.concat([subject_df, onsets], axis=1)
        for k, v in mask_activations.items():
            stable_x[k] = v
        for feat in stable_x.columns:
            stable_x[feat] = stable_x[feat].astype(np.float64)

        volume = guess_volume(pvol, nvol, gvol, t * TR, stable_x, model, masks, norm_info)
        np.save(dst, volume)
