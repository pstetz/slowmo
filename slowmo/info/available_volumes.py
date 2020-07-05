import numpy as np
import nibabel as nib
from tqdm import tqdm

def _mni_brain(filepath="/Volumes/hd_4tb/masks/mni/MNI152_T1_2mm_brain_mask.nii.gz"):
    image = nib.load(filepath)
    data  = image.get_data()
    return data

def create_available_volumes(r=4, output_path="./available_volumes.npy"):
    data = _mni_brain()
    shape = data.shape
    available_volumes = list()
    for i in tqdm(range(r, shape[0] - r)):
        for j in range(r, shape[1] - r):
            for k in range(r, shape[2] - r):
                if data[i, j, k] == 0:
                    continue
                available_volumes.append([i, j, k])
    available_volumes = np.array(available_volumes)
    np.save(output_path, available_volumes)

if __name__ == "__main__":
    create_available_volumes()

