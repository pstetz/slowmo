from glob import glob
from tqdm import tqdm
from utils.os import copy
from os.path import basename, dirname, isfile, join


tasks = [
        ["gambling", "mb", "pe0"],
        ["emotion", "mb", "pe0"],
        ["rest", "mb", "pe0"],
        ["rest", "mb", "pe1"],
        ["wm", "mb", "pe0"],
        ["gonogo", "sb", "pe0"],
        ["conscious", "sb", "pe0"],
        ["nonconscious", "sb", "pe0"],
]

def transfer_func(session_path, subject, session, dst_dir):
    tail = "space-MNI152NLin6Asym_desc-smoothAROMAnonaggr_bold.nii.gz"
    for task_name, mb, direction in tasks:
        filename = f"{subject}_{session}_task-{task_name}_acq-{mb}_dir-{direction}_{tail}"
        tsv_name = f"{subject}_{session}_task-{task_name}_acq-{mb}_dir-{direction}_desc-confounds_regressors.tsv"
        filepath = join(session_path, "func", filename)
        tsv_path = join(session_path, "func", tsv_name)
        if not isfile(filepath): continue
        task_dir = join(dst_dir, subject.replace("sub-", "").lower(), "func", "%s-%s-%s" % (task_name, mb, direction))
        dst = join(task_dir, filename)

        copy(filepath, join(task_dir, filename))
        copy(tsv_path, join(task_dir, tsv_name))

def transfer_anat(subject_path, subject, dst_dir):
    for anat in ["WM", "GM", "CSF"]:
        filename = f"{subject}_space-MNI152NLin6Asym_label-{anat}_probseg.nii.gz"
        src = join(subject_path, "anat", filename)
        if not isfile(src): continue
        dst = join(dst_dir, subject.replace("sub-", "").lower(), "anat", "%s_probseq.nii.gz" % anat.lower())
        copy(src, dst)


def main(root, dst_dir):
    for subject_path in tqdm(glob(join(root, "sub-*/"))):
        subject = basename(dirname(subject_path))

        ## Transfer anatomicals
        transfer_anat(subject_path, subject, dst_dir)

        ## Transfer functionals
        for session_path in glob(join(subject_path, "ses-*/")):
            session = basename(dirname(session_path))
            transfer_func(session_path, subject, session, dst_dir)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    root = "/Users/pstetz/Desktop/server/ramirezc/hcpdes_preprocessed_04-2020/derivatives/functional_derivatives/"
    dst_dir = "/Volumes/hd_4tb/slowmo/data/fmri/connectome"
    main(root, dst_dir)

