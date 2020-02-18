import os
import pickle
import numpy as np
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join

def _save(data, output_path):
    if not isdir(dirname(output_path)):
        os.makedirs(dirname(output_path))
    print("Saving to %s" % output_path)
    with open(output_path, 'wb') as f:
        pickle.dump(data, f, protocol=4)

def consolidate(folders, output_path):
    print("Starting to consolidate %s" % output_path)
    bold_signal, prev_volume, next_volume, info = [], [], [], []
    for folder in tqdm(folders):
        dirs = glob(join(folder, "*"))
        for batch_path in dirs:
            bold_signal.extend(np.load(join(batch_path, "pred.npy")))
            prev_volume.extend(np.load(join(batch_path, "norm_prev.npy")))
            next_volume.extend(np.load(join(batch_path, "norm_next.npy")))
            info.extend(np.load(join(batch_path, "norm_info.npy"), allow_pickle=True))

    print("Converting to numpy array")
    batch = {
            "pred": np.array(bold_signal),
            "prev": np.array(prev_volume),
            "next": np.array(next_volume),
            "info": np.array(info, dtype=np.float32)
    }
    _save(batch, output_path)

if __name__ == "__main__":
    root = "/Volumes/hd_4tb/results"
    training = join(root, "training")
    output_dir = join(root, "summary", "consolidate")

    items = np.array(glob(join(training, "*")))
    np.random.shuffle(items)
    for i, folders in enumerate(np.array_split(items, 20)):
        consolidate(folders, join(output_dir, "all_%02d.pkl" % i))
