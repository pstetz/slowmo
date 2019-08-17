import os
import flywheel

class Cloud:
    def __init__(self):
        API_KEY = os.environ["FLYWHEEL_API"]
        self.fw = flywheel.Flywheel(API_KEY)
        
    def download(self, project, subject, time_session, task):
        ### Find Flwheel project
        fw_project = [p for p in fw.get_all_projects() if p.label == project][0]
        
        ### Get all valid sessions for project
        sessions     = fw.get_project_sessions(project_id)
        sessions     = [s for s in sessions if s.label.isdigit()]
        
        ### Filter by subject and time session
        sessions = self.filter_subject(sessions, subject)
        sessions = self.filter_time_session(sessions, time_session)
        
        ### Find unique task
        ### (NOTE: mark the task as donotuseme if there are multiple)
        task_files = self.get_task_files(sessions)
        if len(task_files) == 0:
            raise Exception("Task %s not found for %s %s %s on Flwheel" % (task, project, subject, time_session))
        
        ### Download the task dicom
        dicom_filename = _get_dicom_filename(task_files)
        self._download_file(acq_id, dicom_filename, output_path)
        
    def _find_project_label(self, session):
        project_id = session.project
        return self.fw.get_project(project_id).label
    
    def _clean_subject(self, subject):
        subject = subject.lower()
        if subject.startswith("rad"):
            return subject.split("-")[0]
        elif subject.startswith("conn"):
            return subject.split("_")[0]
        elif project == "engage"
        
    def _filter_subject(self, sessions, subject):
        subject = subject.lower()
        sessions = [s for s in sessions if self._find_subject(s) == subject]
        return sessions
    
    def _determine_time_session(self, session):
        tag_map = {
            "BV": "000_data_archive",
            "2MO": "2MO_data_archive",
            "3MO": "3MO_data_archive",
            "6MO": "6MO_data_archive",
            "12MO": "12MO_data_archive",
            "24MO": "24MO_data_archive"
        }
        project = self._find_project_label(session).lower()
        if project == "engage":
            subject_id = session.subject.code.upper()
            if subject_id.endswith("12MO"): # check before 2MO.  Be careful!
                return tag_map["12MO"]
            for tag in ("BV", "2MO", "6MO", "24MO"):
                if subject_id.endswith(tag):
                    return tag_map[tag]
            return "000_data_archive"
        elif project == "connectome":
            tags
    
    def _filter_time_session(self, sessions, time_session):
        time_session_map
        
    def _is_match(self, fw_label, task_name):
        fw_label = fw_label.lower().replace(" ", "_").replace("-", "_")
        
        ### Invalid files are never a match
        if "donotuse" in fw_label or "nope" in fw_label:
            return False
        
        ### Check if file matches
        if task_name == "gonogo" and "go_no_go" in fw_label:
            return True
        elif task_name == "conscious" and "conscious" in fw_label and "nonconscious" not in fw_label:
            return True
        elif task_name == "nonconscious" and "nonconscious" in fw_label:
            return True
        return False
    
    def _get_dicom_filename(self, files):
        dicom = [f for f in files if f.name.endswith(".dicom.zip")]
        assert len(dicom) == 1, "Multiple dicoms found"
        return dicom.pop()
    
    def _download_file(self, acq_id, filename, output_path):
        if os.path.isfile(output_path):
            print("%s already exists!  Overwriting..." % output_path)
            os.remove(output_path)
        print("Downloading %s..." % output_path)
        self.fw.download_file_from_acquisition(acq_id, filename, output_path)