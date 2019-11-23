import os
import scipy.io
import pandas as pd
from glob import glob
from os.path import join
from tqdm import tqdm

def _find_discarded_vols(filepath):
    if not os.path.isfile(filepath):
        return 0
    mat = scipy.io.loadmat(filepath)
    return mat["spike_regressors"].sum()

def _task_map(task_folder):
    for code, name in [
        ("101", "gonogo"),
        ("103", "conscious"),
        ("104", "workingmemSB"),
        ("105", "nonconscious"),
        ("1026", "workingmemMB"),
    ]:
        if task_folder.split("_")[0] == code:
            return name;
    return False

def _time_map(time_session):
    _map = {
        "000_data_archive": "s1",
        "2MO_data_archive": "s2",
        "6MO_data_archive": "s3",
        "12MO_data_archive": "s4",
        "24MO_data_archive": "s5",
    }
    if time_session not in _map:
        return False
    return _map[time_session]

def _session_movement(session_path):
    batch = list()
    task_root = join(session_path, "100_fMRI")
    for task_folder in glob(join(task_root, "10*")):
        task = _task_map(os.path.basename(task_folder))
        if not task:
            continue
        spikes_file = join(task_folder, "spike_regressors_wFD.mat")
        discarded_vols = _find_discarded_vols(spikes_file)
        batch.append({"task": task, "discarded_vols": discarded_vols})
    return batch

def _gather_project_movement(root, project_folder):
    rows = list()
    for subject_path in tqdm(glob(join(root, project_folder, "*"))):
        subject = os.path.basename(subject_path)
        for session_path in glob(join(subject_path, "*")):
            time_session = os.path.basename(session_path)
            session = _time_map(time_session)
            if not session:
                continue
            batch = _session_movement(session_path)
            for i in range(len(batch)):
                batch[i]["subject"] = subject.lower().replace("_", "").replace("-", "")
                batch[i]["time_session"] = session
            rows.extend(batch)
    return rows

def create_movement():
    dfs = list()
    root = "/Volumes/group/PANLab_Datasets"
    output_path = "/Volumes/hd_4tb/project/movement/all.csv"
    for project, project_folder in [
        ("connhc", "CONNECTOME/conn_hc/dof-12/data"),
        ("connmdd", "CONNECTOME/conn_mdd/dof-12/data"),
        ("engage", "ENGAGE/data"),
        ("engage_2", "ENGAGE_2/data"),
        ("rad", "RAD/data"),
    ]:
        rows = _gather_project_movement(root, project_folder)
        df = pd.DataFrame(rows)
        df["project"] = project
        dfs.append(df)
    pd.concat(dfs, sort=False).to_csv(output_path, index=False)

if __name__ == "__main__":
    create_movement()

