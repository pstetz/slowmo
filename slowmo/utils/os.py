import os
import shutil
import nibabel as nib
from os.path import basename, dirname, isdir, isfile

def copy(src, dst):
    if not isdir(dirname(dst)):
        os.makedirs(dirname(dst))
    if isfile(dst):
        return
    shutil.copy(src, dst)

def load_volume(fmri, x, y, z, t):
    volume = nii_input(fmri[:, :, :, t], x, y, z)
    return np.array(volume)

def load_masks(mask_dir):
    masks = glob(join(mask_dir, "*"))
    masks = [{
        "code": basename(mask).split("_")[0],
        "data": nib.load(mask).get_data(),
    } for mask in masks]
    return masks

def mean_activation(masks, fmri, grey, t, label):
    activations = dict()
    for mask in masks:
        code, data = mask["code"], mask["data"]
        region = np.multiply(data, fmri[:, :, :, t])
        activations["mean_%s_%s" % (code, label)] = np.mean( np.multiply(grey, region) )
    return activations

def in_mask(masks, x, y, z):
    """
    NOTE: Since the coordinates are an input I will not use this
    """
    result = dict()
    for mask in masks:
        code = mask["code"]
        data = mask["data"]
        result["in_%s" % code] = int(bool(data[x, y, z]))
    return result
