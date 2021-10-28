import os
import numpy as np
import pandas as pd
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join

def get_folders(root):
    folders = list()
    for instance in tqdm(glob(join(root, "*"))):
        for run in range(10):
            folder = join(instance, "%02d" % run)
            assert isfile(join(folder, "info.csv")), folder
            folders.append(folder)
    return folders

def collate(root):
    dfs = list()
    folders = get_folders(root)
    for f in tqdm(folders):
        if not isfile(join(f, "info.csv")): continue
        info = pd.read_csv(join(f, "info.csv"))
        for name in ("csf", "wm", "gm", "prev_1", "prev_2", "next_1", "next_2"):
            image = np.load(join(f, f"{name}.npy"))
            info[name] = image[:, 4, 4, 4]
        info["bold"] = np.load(join(f, "bold.npy"))
        dfs.append(info)
    df = pd.concat(dfs)
    df.drop(["height", "weight"], axis=1, inplace=True) # some heights are strings so just ignore for now
    df.reset_index(drop=True, inplace=True)
    df.to_feather(join(root, "..", "all.feather"))

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    root = args[0]
    collate(root)

