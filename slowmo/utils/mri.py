import numpy as np
import nibabel as nib
from os.path import isfile

def load_image(filepath):
    return nib.as_closest_canonical(nib.load(filepath))

def get_data(image):
    if type(image) == str and isfile(image):
        return load_image(image).get_data()
    return image.get_data()

def std_image(data, axis=3):
    """ Gets the std of the image over time """
    return np.std(data, axis=axis)

def mean_image(data, axis=3):
    """ Gets the mean of the image over time """
    return np.mean(data, axis=axis)

def save_image(data, save_path, affine=None):
    assert not affine is None, "Affine is not specified"
    image = nib.Nifti1Image(data, affine)
    nib.save(image, save_path)

def norm_image(data, mask_data):
    """ Subtracts the mean and divides by the std """
    std_data  = std_image(data)
    mean_data = mean_image(data)
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

def nii_region(data, x, y, z, r = 4, shape="square"):
    assert shape == "square" # A ball would be helpful too
    return data[
        x - r : x + r + 1,
        y - r : y + r + 1,
        z - r : z + r + 1
    ]

def _gen_avail_volumes(shape, radius):
    x_min, x_max = radius, shape[0] - radius
    y_min, y_max = radius, shape[1] - radius
    z_min, z_max = radius, shape[2] - radius
    return np.array([(x, y, z) for x in range(x_min, x_max)
                      for y in range(y_min, y_max)
                      for z in range(z_min, z_max)
           ])
