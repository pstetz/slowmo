import os
import shutil
import pandas as pd
from glob import glob
from os.path import basename, dirname, isdir, isfile, join
import parse_wm
import txt_parser

button = "/share/leanew1/PANLab_Datasets/CONNECTOME/button/"
slowmo = "/oak/stanford/groups/leanew1/users/pstetz/.slowmo/onsets/"

def _clean(task):
    if task.startswith("wm-mb"):
        return "workingmemory_mb"
    elif task.startswith("wm-sb"):
        return "workingmemory_sb"
    return task.split("-")[0]

for subject_path in sorted(glob(join(button, "CON*"))):
    subject = basename(subject_path).lower()
    if not isdir(join(slowmo, subject)): continue
    task = "wm-mb-pe0"
    task = "wm-sb-pe0"
    onsets = join(slowmo, subject, task, "onsets.csv")
    log_dir = join(subject_path, "s1", _clean(task))
    logs = [f for f in glob(join(log_dir, "*")) if isfile(f)]
    if len(logs) == 1 and not isfile(onsets):
        logfile = logs.pop()
        print("Creatings %s\nFrom %s" % (onsets, logfile))
        try:
            if logfile.endswith(".log"):
                parse_wm.parse(logfile, onsets)
            elif logfile.endswith(".txt"):
                txt_parser.txt_parser(logfile, "workingmemSB", onsets)
        except Exception as e:
            print("Could not parse %s" % logfile)
            print(e)
            if isdir(dirname(onsets)):
                shutil.rmtree(dirname(onsets))
            print("--------\n")
    elif len(logs) > 1:
        print("Duplicates in %s" % log_dir)

