import nibabel as nib
from os.path import isfile

def load(filepath):
    return nib.as_closest_canonical(nib.load(filepath))

def get_data(image):
    if type(image) == str and isfile(image):
        return load(image).get_data()
    return image.get_data()

def load_volume(fmri, x, y, z, t):
    volume = nii_input(fmri[:, :, :, t], x, y, z)
    return np.array(volume)

def load_masks(mask_dir):
    masks = glob(join(mask_dir, "*"))
    masks = [{
        "code": os.path.basename(mask).split("_")[0],
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

def nii_region(data, x, y, z, r = 4, shape="square"):
    assert shape == "square" # A ball would be helpful too
    return data[
        x - r : x + r + 1,
        y - r : y + r + 1,
        z - r : z + r + 1
    ]

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
