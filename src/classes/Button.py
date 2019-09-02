import os
import pandas as pd
from tqdm import tqdm
from glob import glob
from os.path import join

class Button:
    def __init__(self):
        self.onsets = list()

    def find_all_logs(self, studies):
        for study in studies:
            study_root = self._get_study_root(study)
            self.find_study_logs(study, study_root)

    def find_study_logs(self, study, study_root):
        for subject_path in tqdm(glob(join(study_root, "*"))):
            subject = os.path.basename(subject_path)
            for time_session_path in glob(join(subject_path, "*")):
                time_session = os.path.basename(time_session_path)
                self.find_subject_session_logs(study, subject, time_session, time_session_path)

    def find_subject_session_logs(self, study, subject, time_session):
        study = self._connectome_hc_mdd(study, subject)
        study_root = self._get_study_root(study)
        fmri_folder = join(study_root, subject.upper(), time_session, "100_fMRI")
        task_paths  = glob(join(fmri_folder, "10*"))
        for task_path in task_paths:
            task = self._determine_task_name(task_path)
            onsets = Onsets(study, subject, time_session, task_path, task)
            self.onsets.append(onsets)

    def get(self, study=None, subject_id=None, time_session=None, task=None):
        onsets = self.onsets
        onsets = [button for button in onsets if button.valid]
        if study:
            onsets = [button for button in onsets if button.study == study]
        if subject_id:
            onsets = [button for button in onsets if button.subject_id == subject_id]
        if time_session:
            onsets = [button for button in onsets if button.time_session == time_session]
        if task:
            onsets = [button for button in onsets if button.task == task]
        return onsets

    def _connectome_hc_mdd(self, study, subject):
        subject = subject.lower()
        if not subject.startswith("conn"):
            return study
        if subject.startswith("conn0"):
            return "conn_hc"
        elif subject.startswith("conn1") or subject.startswith("conn2"):
            return "conn_mdd"
        raise Exception("Cannot determine study for subject %s" % subject)

    def _determine_task_name(self, task_path):
        folder_name = os.path.basename(task_path)
        task_map = {
                "101_fMRI_preproc_GO_NO_GO": "gonogo",
                "103_fMRI_preproc_FACES-CONSCIOUS": "conscious",
                "105_fMRI_preproc_FACES-NONCONSCIOUS": "nonconscious",
        }
        return task_map[folder_name]

    def _get_study_root(self, study):
        data_root = "/Volumes/group/PANLab_Datasets"
        study_path_map = {
            "RAD": join(data_root, "RAD", "data"),
            "ENGAGE": join(data_root, "ENGAGE", "data"),
            "ENGAGE_2": join(data_root, "ENGAGE_2", "data"),
            "CONN_HC": join(data_root, "CONNECTOME", "conn_hc", "dof-6", "data"),
            "CONN_MDD": join(data_root, "CONNECTOME", "conn_mdd", "dof-6", "data"),
        }
        return study_path_map[study.upper()]


class Onsets:
    def __init__(self, project, subject, time_session, onset_folder, task):
        self.project = project
        self.subject = subject
        self.time_session = time_session
        self.onset_folder = onset_folder
        self.task = task

        self.find_onsets()
        self.check_onsets()

    def find_onsets(self):
        onsets = glob(join(self.onset_folder, "*.csv"))
        self.onset_paths = [ons for ons in onsets]
        return self.onset_paths

    def check_onsets(self):
        if self.task == "gonogo":
            self.valid = (len(self.onset_paths) == 2)
        elif self.task == "conscious" or self.task == "nonconscious":
            self.valid = (len(self.onset_paths) == 6)
        return False

    def _determine_onset(self, filepath):
        filename = os.path.basename(filepath).lower()
        filename = filename.replace("_onsets.csv", "")
        return filename

    def combine_onsets(self):
        dfs = list()
        for path in self.onset_paths:
            tmp = pd.read_csv(path)
            tmp["onset"] = self._determine_onset(path)
            dfs.append(tmp)
        df = pd.concat(dfs)
        df.sort_values("num", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

