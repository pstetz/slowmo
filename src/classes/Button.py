import os
from glob import glob
from os.path import join

class Button:
    def __init__(self, studies):
        self.studies = studies
        self.buttons = list()
        self.find_logs()
    
    def find_all_logs(self):
        for study in studies:
            study_root = self.get_study_root(study)
            self.find_study_logs(study, study_path)
            
    def find_study_logs(self, study_path):
        for subject_path in glob(join(study_path, "*")):
            subject = os.path.basename(subject_path)
            for time_session_path in glob(join(subject_path, "*")):
                time_session = os.path.basename(time_session_path)
                self.find_subject_session_logs(self, study, subject, time_session, time_session_path)
                
    def find_subject_session_logs(self, study, subject, time_session, time_session_path):
        fmri_folder = join(time_session_path, "100_fMRI")
        task_paths  = glob(join(fmri_folder, "10*"))
        for task_path in task_paths:
            task = self.determine_task_name(task_path)
            onsets = Onsets(task_path, task, study, subject, time_session)
            self.buttons.append(onsets)
    
    def _get(self, study=None, subject_id=None, time_session=None, task=None):
        buttons = self.buttons
        buttons = [button for button in button if button.valid]
        if study:
            buttons = [button for button in buttons if button.study == study]
        if subject_id:
            buttons = [button for button in buttons if button.subject_id == subject_id]
        if time_session:
            buttons = [button for button in buttons if button.time_session == time_session]
        if task:
            buttons = [button for button in buttons if button.task == task]
        return buttons
        
    def get_study_root(self, study):
        study_path_map = {
            "RAD": "/Volumes/group/PANLab_Datasets/RAD/data",
            "ENGAGE": "/Volumes/group/PANLab_Datasets/ENGAGE/data",
            "ENGAGE_2": "/Volumes/group/PANLab_Datasets/ENGAGE_2/data"
            "CONN_HC": "/Volumes/group/PANLab_Datasets/CONNECTOME/conn_hc/data",
            "CONN_MDD": "/Volumes/group/PANLab_Datasets/CONNECTOME/conn_mdd/data",
        }
        return study_path_map[study]
    
    
class Onsets:
    def __init__(self, onset_folder, task):
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