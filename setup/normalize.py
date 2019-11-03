import os
import numpy as np
import nibabel as nib
from glob import glob
from tqdm import tqdm
from os.path import join

def _std(data, axis=3):
    """ Gets the std of the image over time """
    return np.std(data, axis=axis)

def _mean(data, axis=3):
    """ Gets the mean of the image over time """
    return np.mean(data, axis=axis)

def _norm(data, mask_data):
    """ Subtracts the mean and divides by the std """
    std_data  = _std(data)
    mean_data = _mean(data)
    norm_data = np.zeros(data.shape)
    for t in range(norm_data.shape[3]):
        ### Surpress errors from dividing by 0, Inf, or NaN
        ### https://stackoverflow.com/a/23116937/9104642
        with np.errstate(divide='ignore', invalid='ignore'):
            norm_data[:, :, :, t] = np.divide(
                    np.multiply(
                        np.subtract(
                            data[:, :, :, t],
                            mean_data),
                        mask_data
                    ),
                    std_data
                )
    norm_data[np.isnan(norm_data)] = 0
    return norm_data.astype(np.float32)

def _normalize(src, dst, mask):
    """ Normalizes and saves the brain image """

    ### Load data
    image  = nib.load(src)
    affine = image.affine
    data   = image.get_data()

    ### Calculate the normalized data
    mask_data = nib.load(mask).get_data()
    norm_data = _norm(data, mask_data)

    ### Create and save norm image
    norm_image = nib.Nifti1Image(norm_data, affine)
    nib.save(norm_image, dst)

def normalize_project(root, project, mask):
    """ Normalizes all warped.nii.gz images in a project """
    for time_path in glob(join(root, project, "*")):
        for subject_path in tqdm(glob(join(time_path, "*"))):
            for task_path in glob(join(subject_path, "*")):
                src = join(task_path, "warped.nii.gz")
                dst = join(task_path, "normalized.nii.gz")
                if not os.path.isfile(src):
                    continue
                if os.path.isfile(dst):
                    continue
                try:
                    _normalize(src, dst, mask)
                except Exception as e:
                    print(e)
                    print("src", src)
                    print("dst", dst)


if __name__ == "__main__":
    root = "/Volumes/hd_4tb/raw"
    mask = "/Volumes/hd_4tb/masks/mni/MNI152_T1_2mm_brain_mask.nii.gz"
    projects = ["connhc", "connmdd", "engage", "engage2", "rad"]
    for project in projects:
        normalize_project(root, project, mask)
