import os
from glob import glob
from tqdm import tqdm
from os.path import basename, isfile, join
from helpers.mri import load_image, save_image, get_data, norm_image

def normalize_over_time(src, dst):
    """ Normalizes and saves the brain image """
    mask = "/Volumes/hd_4tb/slowmo/data/masks/mni/MNI152_T1_2mm_brain_mask.nii.gz"

    image  = load_image(src)
    data   = get_data(image)
    mask_data = get_data(mask)

    norm_data = norm_image(data, mask_data)
    save_image(norm_data, dst, affine=image.affine)

def normalize_project(root):
    for subject_path in tqdm(glob(join(root, "*"))):
        for task_path in glob(join(subject_path, "func", "*")):
            tail = "_space-MNI152NLin6Asym_desc-smoothAROMAnonaggr_bold.nii.gz"
            matches = glob(join(task_path, f"*{tail}"))
            for src in matches:
                filename = basename(src).replace(tail, "_standardized.nii.gz")
                filename = "_".join(filename.split("_")[1:]) # remove subject info
                dst = join(task_path, filename)
                if isfile(dst): continue
                normalize_over_time(src, dst)


if __name__ == "__main__":
    root = "/Volumes/hd_4tb/slowmo/data/fmri/connectome"
    normalize_project(root)
