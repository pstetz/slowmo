import os
import sys
from tqdm import tqdm
from glob import glob
from os.path import basename, dirname, isdir, isfile, join
from slowmo.utils.os import copy

tasks = {
        "gonogo": "gonogo-sb-pe0",
        "conscious": "conscious-sb-pe0",
        "nonconscious": "nonconscious-sb-pe0",
        "workingmemory_mb": "wm-mb-pe0",
        "workingmemory_sb": "wm-sb-pe0",
        "guessing": "gambling-mb-pe0",
        "emotion": "emotion-mb-pe0",
}
def transfer(root, dst_dir):
    for subject_path in tqdm(glob(join(root, "CONN*"))):
        subject = basename(subject_path).lower()
        for task in tasks:
            onset_file = join(subject_path, "s1", task, "key_onsets/onsets.csv")
            if not isfile(onset_file): continue
            dst = join(dst_dir, subject, tasks[task], "onsets.csv")
            copy(onset_file, dst)

if __name__ == "__main__":
    root = "/share/leanew1/PANLab_Datasets/CONNECTOME/button"
    dst_dir = "/oak/stanford/groups/leanew1/users/pstetz/.slowmo/onsets"
    transfer(root, dst_dir)

