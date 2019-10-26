import numpy as np
import pandas as pd
from tqdm import tqdm
from DicomDir import DicomDir
from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager

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
    return np.array([(x, y, z) for x in range(x_min, x_max)
                      for y in range(y_min, y_max)
                      for z in range(z_min, z_max)
           ])

def _add_map(data, _map):
    for key in _map:
        _add_value(data, key, _map[key])

def _add_value(data, key, value):
    if not key in data:
        data[key] = list()
    data[key].append(value)

def most_recent_onset(df, onset_names, time):
    df = df[df.ons < time]
    most_recent = dict()
    for name in onset_names:
        tmp = df[df.onset == name]
        recent_ons = tmp.tail(1)["ons"].values
        if len(recent_ons) == 0:
            most_recent[name] = time - 100 # Put the onset time to 100 seconds in the past
        else:
            most_recent[name] = recent_ons[0]
    return most_recent

def recent_onsets(df, trigger_time):
    onset_names = df.onset.unique()
    time = trigger_time / 1000
    recent_onset = most_recent_onset(df, onset_names, time)
    onset_diff = {k: v - trigger_time/1000 for k, v in recent_onset.items()}
    return onset_diff

def _format_onsets(onsets):
    all_onsets = ["go", "nogo", "anger", "happy", "neutral", "fear", "disgust", "sad"]
    for onset in all_onsets:
        if onset not in onsets:
            onsets[onset] = -100
    return onsets

def gen_data(manager, dicoms, num_volume, onsets,
        radius=5, percent_sample=0, low_memory=True,
        num_processes=50):
    avail_volumes = _gen_avail_volumes(dicoms.shape, radius)
    onset_df = onsets.combine_onsets()

    ### Restrict to sample
    if percent_sample:
        N = len(avail_volumes)
        idx = np.random.randint(N, size=int(N * percent_sample))
        avail_volumes = avail_volumes[idx, :]

    ### Generate dataframe
    data    = dict()
    batch   = manager.list([[]]*num_processes)
    processes = list()

    ### Batch, parallel data generation
    for x, y, z in tqdm(avail_volumes):
        if len(processes) == num_processes:
            [p.join() for p in processes]
            processes = list()
            _combine_batch(data, batch)
            batch = manager.list([[]]*num_processes)

        process = Process(target=_gen_curr_row, args=(batch, len(processes), dicoms, x, y, z, onset_df, num_volume, radius))
        processes.append(process)
        process.start()

    df = pd.DataFrame(data)
    if low_memory:
        df = _convert_float64_to_float32(df)
    return df

def _combine_batch(data, batch):
    for row in batch:
        _add_map(data, row)

def _gen_curr_row(
        batch, i,
        dicoms, x, y, z,
        onset_df,
        num_volume, radius
        ):

    curr_volume   = dicoms.get_volume(num_volume)
    trigger_time = dicoms.get_trigger_time(z, num_volume)

    ### fMRI data
    _prev = _volume_data(dicoms, x, y, z, num_volume, -1, radius)
    _next = _volume_data(dicoms, x, y, z, num_volume, 1,  radius)
    curr_row = {**_prev, **_next}
    curr_row["time"]   = trigger_time
    curr_row["x"]      = x
    curr_row["y"]      = y
    curr_row["z"]      = z
    curr_row["signal"] = curr_volume[x, y, z]

    ### Stimuli
    stimuli = recent_onsets(onset_df, trigger_time)
    stimuli = _format_onsets(stimuli)

    ### Add to batch
    batch[i] = curr_row

def gather():
    BaseManager.register('DicomDir', DicomDir)
    manager = BaseManager()
    manager.start()

    dicom_path = "/Users/pbezuhov/tmp/engage-PA30563-000_data_archive-gonogo"

    ### Load dicoms and cut the first 3 volumes
    fmri_data = manager.DicomDir(dicom_path)
    fmri_data.cut_volumes(3)

    for num_volume in range(1, fmri_data.num_volumes - 2):
        print("Generating data for volume %d" % num_volume)

        ### Generate the training data from all the features
        df = gen_data(manager, fmri_data, num_volume, onsets)

def _convert_float64_to_float32(df):
    for col in tqdm(df.columns):
        if df[col].dtype == np.float64:
            df[col] = df[col].astype(np.float32)
    return df

