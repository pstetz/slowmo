import os
import ast
import json
import numpy as np
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join

def norm_grey_matter(root, stats_file):
    if not isfile(stats_file):
        find_subject_stats(root, stats_file)
    mn, std = _find_mean_std(stats_file)
    for t in ("prev", "next"):
        print("Normalizing %s..." % t)
        for f in tqdm(glob(join(root, "*", "*", "%s.npy" % t))):
            output_path = join(dirname(f), "norm_%s.npy" % t)
            data = np.load(f)
            if isfile(output_path):
                continue
            data[:, :, :, :, 1] = np.divide(np.subtract(data[:, :, :, :, 1], mn), std)
            np.save(output_path, data)

def _find_mean_std(stats_file):
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

def find_subject_stats(root, stats_file):
    folders  = glob(join(root, "*"))
    subjects = [basename(f) for f in folders]
    norm_info = dict()
    for subject in tqdm(subjects):
        for item in glob(join(root, subject, "*", "prev.npy")):
            sub = basename(dirname(item))
            grey_matter = np.load(item)
            grey_matter = grey_matter.flatten()
            k = "%s-%s" % (subject, sub)
            norm_info[k] = dict()
            norm_info[k]["mean"] = grey_matter.mean()
            norm_info[k]["std"]  = grey_matter.std()
    norm_info = json.dumps(str(norm_info))
    with open(stats_file, "w") as f:
        json.dump(norm_info, f)

if __name__ == "__main__":
    root = "/Volumes/hd_4tb/results/training"
    stats_file = "./grey_norm.json"
    norm_grey_matter(root, stats_file)

