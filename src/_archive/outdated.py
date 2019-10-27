

"""
Decided to use a square as input rather than
something spherical
"""
def voxel_radius(radius):
    valid = list()
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
    return valid

"""
Instead of using a CSV as input, I'll have 3 different inputs
"""
def _volume_data(dicoms, x, y, z, t, direction, radius):
    row = dict()
    volume = dicoms.get_volume(t + direction)
    for coord in voxel_radius(radius):
        i, j, k  = coord["x"], coord["y"], coord["z"]
        loc      = "i%d_j%d_k%d_t%d" % (i, j, k, direction)
        row[loc] = volume[x+i, y+j ,z+k]
    return row

"""
I'll have the validator in the notebook
"""
def _valid_patient(patient, dicom_path, button, logger):
    """ FIXME: finish me """
    valid = True
    if not patient:
        logger.log()
        valid = False
    if not dicom_path:
        logger.log()
        valid = False
    if not button:
        logger.log()
        valid = False
    return valid
