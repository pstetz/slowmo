import pandas as pd

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

def _train_task(project, task, onsets, data, patient, is_ascending):
    for num_volume in len(data.shape[-1]):
        df = _gen_data(project, task, onsets, volume, patient, is_ascending, num_volume)
        model.train(df)

def _volume_data(dicoms, x, y, z, t, direction, radius):
    row = dict()
    volume = dicoms.get_volume(t + direction)
    for coord in voxel_radius(radius):
        i, j, k  = coord["x"], coord["y"], coord["z"]
        loc      = "i%d_j%d_k%d_t%d" % (i, j, k, direction)
        row[loc] = volume[x+i, y+j ,z+k]
    return row

def _gen_avail_volumes(shape, radius):
    x_min, x_max = radius, shape[0] - radius
    y_min, y_max = radius, shape[1] - radius
    z_min, z_max = radius, shape[2] - radius
    return [(x, y, z) for x in range(x_min, x_max)
                      for y in range(y_min, y_max)
                      for z in range(z_min, z_max)
           ]

def _gen_data(project, task, onsets, dicoms, patient, is_ascending, num_volume, radius=5):
    avail_volumes = _gen_avail_volumes(dicoms.shape, radius)
    curr_volume   = dicoms.get_volume(num_volume)
    rows = list()
    for x, y, z in tqdm(avail_volumes):
        _prev = _volume_data(dicoms, x, y, z, num_volume, -1, radius)
        _next = _volume_data(dicoms, x, y, z, num_volume, 1,  radius)
        row = {**_prev, **_next}
        row["signal"] = curr_volume[x, y, z]
        row["x"] = x
        row["y"] = y
        row["z"] = z
        rows.append(row)
    df = pd.DataFrame(rows)

    ### patient data
#     df["age"] = patient.age
#     df["is_female"] = (patient.gender == "female")

    ### Project data
    df["is_rad"]        = int(project == "rad")
    df["is_engage"]     = int(project == "engage")
    df["is_connectome"] = int(project == "connectome")

    ### task data
    df["is_gng"] = int(task == "gonogo")
    df["is_fc"]  = int(task == "conscious")
    df["is_fnc"] = int(task == "nonconscious")

    ### fMRI data
    df["is_ascending"] = int(is_ascending)
    return df

