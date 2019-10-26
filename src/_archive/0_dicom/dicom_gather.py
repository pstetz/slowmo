
from DicomDir import DicomDir
from multiprocessing import Process, Manager
from multiprocessing.managers import BaseManager

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
