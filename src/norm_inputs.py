import os
import numpy as np
import pandas as pd

from glob import glob
from os.path import dirname, join
from tqdm import tqdm

def _load(files):
    print("Loading avaiable files...")

    data = list()
    for f in tqdm(files):
        data.extend(np.load(f, allow_pickle=True))
    np_data = np.array(data)
    return np_data

def _input_info(data):
    print("Gathering mean and std information...")

    cols = dict()
    for i in tqdm(range(data.shape[1])):
        feature_data = data[:,i]
        cols[i] = dict()
        if i < 13: # change the onset times to be between 0s and 15s
            feature_data = np.clip(feature_data, 0, 15)
        cols[i]["mean"] = np.mean(feature_data)
        cols[i]["std"]  = np.std( feature_data)
    return cols

def _norm(f, cols, overwrite=True):
    output_path = jojn(dirname(f), "norm_info.npy")
    if isfile(output_path) and overwrite:
        os.remove(output_path)
    elif isfile(output_path):
        return

    data = np.load(f, allow_pickle=True)
    for i in cols:
        row = data.copy()[:, i]
        if cols[i]["std"] != 0:
            data[:, i] = np.divide(np.subtract(row, cols[i]["mean"]), cols[i]["std"])
    np.save(output_path, data)

def normalize():
    files = glob(join("/Volumes/hd_4tb/results/training/*/*/info.npy"))

    ### Get mean/std of training data
    data = _load(files)
    cols = _input_info(data)

    print("Normalizing available files...")
    for f in tqdm(files):
        _norm(f, cols)

if __name__ == "__main__":
    normalize()

