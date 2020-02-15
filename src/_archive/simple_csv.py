import os
import json
import numpy as np
import pandas as pd
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join

def create_simple_csv(root, np_key):
    files = glob(join(root, "*", "*", "2_fix_info.npy"))
    for f in tqdm(files):
        dst = join(dirname(f), "simple.csv")
        if isfile(dst):
            continue
        data = np.load(f, allow_pickle=True)
        columns = dict()
        for i in np_key.keys():
            columns[np_key[i]] = data[:, int(i)]
        _prev, _next, _grey = _get_fmri(f)
        columns["prev"] = _prev
        columns["next"] = _next
        columns["grey"] = _grey
        pd.DataFrame(columns).to_csv(dst, index=False)

def _get_fmri(filepath):
    prev_data = np.load(join(dirname(filepath), "prev.npy"))
    next_data = np.load(join(dirname(filepath), "next.npy"))
    _prev = prev_data[:, 4, 4, 4, 0]
    _next = next_data[:, 4, 4, 4, 0]
    _grey = next_data[:, 4, 4, 4, 1]
    return _prev, _next, _grey

if __name__ == "__main__":
    root = "/Volumes/hd_4tb/results/training"
    np_key = join(root, "..", "summary", "info_order.json")
    with open(np_key, "r") as f:
        np_key = json.load(f)
    create_simple_csv(root, np_key)

