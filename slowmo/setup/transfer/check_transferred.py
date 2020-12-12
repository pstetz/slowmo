import os
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isdir, isfile, join

TASKS = [
    "conscious-sb-pe0",
    "emotion-mb-pe0",
    "gambling-mb-pe0",
    "gonogo-sb-pe0",
    "nonconscious-sb-pe0",
    "wm-mb-pe0",
    "wm-sb-pe0"
]
REGEX = "_desc-smoothAROMAnonaggr_bold.nii.gz"

def get_onsets():
    onsets = set()
    folder = "/oak/stanford/groups/leanew1/users/pstetz/.slowmo/onsets"
    for subject_path in tqdm(glob(join(folder, "*"))):
        subject = basename(subject_path)
        for task in TASKS:
            if isfile(join(subject_path, task, "onsets.csv")):
                onsets.add(f"{subject}_{task}")
    return onsets

def get_fmri():
    fmri = set()
    folder = "/oak/stanford/groups/leanew1/ramirezc/hcpdes_latest/derivatives/functional_derivatives/fmriprep"
    for subject_path in tqdm(glob(join(folder, "sub-CON*"))):
        if not isdir(subject_path): continue
        subject = basename(subject_path).replace("sub-", "").lower()
        for task in TASKS:
            taskname = task.split("-")[0]
            acq = task.split("-")[1]
            matches = set()
            search = join(subject_path, "ses-00", "func", f"*task-{taskname}*acq-{acq}*{REGEX}")
            matches = glob(search)
            matches = [m for m in matches if "ses-00" in basename(m) or "ses-01" in basename(m)]
            if len(matches) > 1:
                print("Check duplicates for:", search)
                continue
            if len(matches) == 1:
                fmri.add(f"{subject}_{task}")
                #print(f"{subject}_{task}")
    return fmri

def main():
    onsets = get_onsets()
    fmri = get_fmri()
    for task in fmri:
        if "rest" in task:
            fmri.remove(task)
    diff = fmri - onsets
    print(diff)
    diff = [d.split("_")[1] for d in diff]
    from collections import Counter
    print(Counter(diff))

if __name__ == "__main__":
    main()

