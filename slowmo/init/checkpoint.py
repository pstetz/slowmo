def append_anat(anat, batch, x, y, z):
    for name in anat:
        batch[name].append(img_region(anat[name], x, y, z, r=RADIUS))

def append_func(fmri, batch, x, y, z, t):
    for name, timepoint in [
            ("prev_1", t-1), ("prev_2", t-2),
            ("next_1", t+1), ("next_2", t+2)
            ]:
        batch[name].append(img_region(fmri[:, :, :, timpoint], x, y, z, r=RADIUS))

def append_mris():
    row = mask_info(masks, fmri, grey, (x, y, z, t))
    for name, value in [("x", x), ("y", y), ("z", z), ("t", t)]:
        row[name] = value
    info["mri"].append(row)

def checkpoint()
    info_df = combine_info(info)
    if not isdir(input_folder):
        os.makedirs(input_folder)
    batch["info"] = pd.concat([
        onsets, info, pd.DataFrame(mask_rows)
    ], axis=1)

    for name in batch:
        arr = np.array(batch[name])
        np.save(join(input_folder, f"{name}.npy"), arr)
        batch[name].clear()

    np.save(join(input_folder, "bold.npy"), np.array(bold_signal))

    info_df.to_csv
    bold_signal.clear(); mask_rows.clear(); onsets.clear()


def append_onsets()
    onsets.append(last_onset(onset_df, task, TR * t, max_time=1000))

def append_voxel(fmri, anat, info, bold, batch, x, y, z, t)
    bold.append(fmri[x, y, z, t])
    append_anat(anat, batch, x, y, z)
    append_func(fmri, batch, x, y, z, t)
    append_mri(fmri, anat, info, x, y, z, t)
    append_onsets(fmri, info, t)

def last_save(training_path):
    training = glob(join(training_path, "*"))
    if len(training) == 0:
        return 0
    i = max(training)
    i = os.path.basename(i)
    return int(i) + 1
