import os
from glob import glob
from tqdm import tqdm
from os.path import basename, dirname, isfile, join
from slowmo.utils.fsl_command import fsl_command

def resample(filepath):
    reference = "/Volumes/hd_4tb/slowmo/data/masks/mni/MNI152_T1_2mm_brain_mask.nii.gz"
    dst = join(dirname(filepath), basename(filepath).replace(".nii.gz", "_resampled.nii.gz"))
    if isfile(dst): return
    fsl_command("flirt", "-in", filepath, "-ref", reference, "-out", dst, "-applyxfm")

def resample_anat_probseg(root):
    for anat in ["gm", "wm", "csf"]:
        print(f"Resampling {anat}")
        for subject_path in tqdm(glob(join(root, "conn*"))):
            filepath = join(subject_path, "anat", f"{anat}_probseg.nii.gz")
            if not isfile(filepath): continue
            resample(filepath)

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    root = args[0]
    resample_anat_probseg(root)
