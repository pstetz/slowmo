def main(masks_dir, masks_path):
    with open(masks_path) as f:
        mask_names = f.readlines()
        mask_names = [m[:-1] for m in mask_names] # remove \n character
    masks = [os.path.join(masks_dir, m + ".nii") for m in mask_names]
    return masks

def get_data(filepath):
    assert os.path.isfile(filepath), "%s does not exist"
    image = nib.load(fn)
    return nib.as_closest_canonical(image)

def mask_image(image, mask):
    if len(image.shape) == 3:
        return np.multiply(image, mask)
    assert len(image.shape) == 4, "%s is not a valid image shape." % str(image.shape)

    masked_imaged = image.copy()
    for i in range(image.shape[3]):
        masked_image[i] = np.multiply(image[i], mask)
    return masked_image

def mask_mean_std(image, mask):
    """ FIXME: might want to norm each voxel before taking the mean/std """
    masked_image = mask_image(image, mask)
    return mask_image.mean(), mask_image.std()

def norm_voxel(data, x, y, z, t):
    assert len(data.shape) == 4, "The dimension size should be 4 not %s" % str(data.shape)
    voxel = data[x, y, z, :]
    return (voxel[t] - voxel.mean()) / voxel.std()

def trainable_mask(mask, radius):
    """ Given a mask determine what voxels are [radius] away from the outside """
    trainable_mask = mask.copy()
    x_size, y_size, z_size = mask.shape
    for x in range(x_size):
        for y in range(y_size):
            for z in range(z_size):
                if mask[x, y, z] == 0:
                    continue
                if not within_radius(mask, x, y, z, radius):
                    trainable_mask[x, y, z] = 0
    return trainable_mask

def voxel_radius(radius):
    valid = list()
    count = 0

    for i in range(radius+1):
        for j in range(radius+1):
            for k in range(radius+1):
                if i == 0 and j == 0 and k == 0:
                    continue
                if i**2 + j**2 + k**2 > radius**2:
                    continue

                for parity in ([1, 1, 1], [-1, 1, 1], [1, -1, 1], [1, 1, -1],
                               [-1, -1, 1], [-1, 1, -1], [1, -1, -1], [-1, -1, -1]):
                    if ((i == 0 and parity[0] == -1) or
                        (j == 0 and parity[1] == -1) or
                        (k == 0 and parity[2] == -1)):
                        continue
                    valid.append({"x":  i * parity[0], "y":  j * parity[1], "z":  k * parity[2]})
    print(len(valid), (2 * radius + 1)**3)
    return valid
#     return count, (2 * radius + 1)**3
