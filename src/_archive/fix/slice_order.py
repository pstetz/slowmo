"""
The slice order for RAD wasn't merged correctly so the info for all tasks is missing
"""
import numpy as np
import pandas as pd
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isfile, join

def keypress_fix(root):
    df = pd.read_csv(join(root, "..", "summary", "model_input.csv"))
    files = glob(join(root, "*", "*", "fix_info.npy"))

    for f in tqdm(files):
        i = int(basename(dirname(dirname(f))))
        asc, des = _sample_info(df, i)

        try:
            _fix_file(f, asc, des)
        except Exception as e:
            print(e)
            print(f)

def _time_map():
    _map = {
        "s1": "000",
        "s2": "2MO",
        "s3": "6MO",
        "s4": "12MO",
        "s5": "24MO",
    }
    return _map

def _sample_info(df, i):
    asc = df.loc[i, "is_ascending"]
    des = df.loc[i, "is_descending"]
    return asc, des

def _fix_file(filepath, asc, des):
    asc_i, des_i = 14, 20
    new_path = join(dirname(filepath), "2_" + basename(filepath))
    if isfile(new_path):
        return
    data = np.load(filepath, allow_pickle=True)
    data[:, asc_i] = int(asc)
    data[:, des_i] = int(des)
    np.save(new_path, data)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if len(args) == 0:
        root = "/Volumes/hd_4tb/results/training"
    else:
        root = args.pop()
    assert len(args) == 0, "inappropriate arguments %s" % " ".join(sys.argv)
    keypress_fix(root)

