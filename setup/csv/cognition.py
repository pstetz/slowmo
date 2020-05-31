def _files_exist(folder, filenames):
    for filename in filenames:
        filepath = join(folder, filename)
        if not os.path.isfile(filepath):
            return False
    return True

def _has_structural(subject_path):
    needed = ["gm_probseg.nii.gz", "subject_to_MNI_warp.nii.gz"]
    return _files_exist(join(subject_path, "structural"), needed)

def _get_tasks(subject_path):
    tasks = glob(join(subject_path, "*"))
    tasks = [os.path.basename(task_path) for task_path in tasks]
    return [task for task in tasks if task != "structural"]

def _validate_subject_task(subject_path, task):
    needed = ["onsets.csv", "normalized.nii.gz"]
    if not _has_structural(subject_path):
        return False
    return _files_exist(join(subject_path, task), needed)

def _get(row, item):
    return row[item]

def _consolidate(row):
    ### Setup
    project      = _get(row, "project")
    subject      = _get(row, "subject")
    task         = _get(row, "task")

    ### Init info
    info = {
        "project":      project,
        "subject":      subject,
        "time_session": time_session,
        "task":         task
    }

    ### fMRI
    info["is_mb"] = is_mb

    ### Task
    for task_name in ["gonogo", "conscious", "nonconscious", "workingmem"]:
        info["is_%s" % task_name] = _is_task(task, task_name)

    ### Project
    for study in ["connhc", "connmdd", "engage", "rad"]:
        info["is_%s" % study] = project == study

    ### Age, Gender
    info["age"] = _get(row, "age")
    info["is_male"] = _get(row, "gender") == "male"
    info["is_female"] = _get(row, "gender") == "female"
    return info

info_csv = "/Volumes/hd_4tb/project/info.csv"
info = pd.read_csv(info_csv)
full = pd.merge(df, info, on=["project", "subject", "time_session", "task"], how="left")
full = full[((full.age.notnull()) & (full.gender.notnull()))]
