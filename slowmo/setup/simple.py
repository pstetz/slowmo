import os
import numpy as np
import pandas as pd
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join

def collate(root):
    dfs = list()
    for instance in tqdm(glob(join(root, "*"))):
        for run in glob(join(instance, "*")):
            if isfile(join(run, "simple.csv")): continue
            if not isfile(join(run, "info.csv")): continue
            info = pd.read_csv(join(run, "info.csv"))
            for name in ("csf", "wm", "gm", "prev_1", "prev_2", "next_1", "next_2"):
                image = np.load(join(run, f"{name}.npy"))
                info[name] = image[:, 4, 4, 4]
            info["bold"] = np.load(join(run, "bold.npy"))
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

"""
NOTES:

This might be helpful to fix height
height_map = {"5'9": 175.26, "5'10\"": 177.8, "5'11": 180.34}

Unfortunately conn152 has 60 which might be either 160cm or 60in, both reasonable
"""
