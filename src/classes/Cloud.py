import os
import flywheel
from os.path import join

class Cloud:
    def __init__(self):
        API_KEY = os.environ["FLYWHEEL_API"]
        self.fw = flywheel.Flywheel(API_KEY)

    """
    Downloading
    """
    def download(self, project, subject, time_session, task, output_directory="/Users/pbezuhov/tmp"):
        ### Find Flwheel project
        fw_project = [p for p in self.fw.get_all_projects() if p.label == project][0]

        ### Get all valid sessions for project
        sessions     = self.fw.get_project_sessions(fw_project.id)
        sessions     = [s for s in sessions if s.label.isdigit()]

        ### Filter by subject and time session
        sessions = self._filter_subject(sessions, subject)
        sessions = self._filter_time_session(sessions, time_session)

        ### Find unique task
        ### (NOTE: mark the task as donotuseme if there are multiple)
        acq_ids = self._get_task_files(sessions, task)
        if len(acq_ids) == 0:
            raise Exception("Task %s not found for %s %s %s on Flwheel" % (task, project, subject, time_session))
        if len(acq_ids) != 1:
            raise Exception("Multiple task %s found for %s %s %s on Flwheel" % (task, project, subject, time_session))
        acq_id = acq_ids.pop()

        ### Download the task dicom
        output_path = join(output_directory, "%s-%s-%s-%s.dicom.zip" % (project, subject, time_session, task))
        dicom_filename = self._get_dicom_filename(acq_id)
        self._download_file(acq_id, dicom_filename, output_path)
        return output_path

    def _download_file(self, acq_id, filename, output_path):
        if os.path.isfile(output_path):
            print("%s already exists!  Overwriting..." % output_path)
            os.remove(output_path)

        ### Create folder if does not exist
        output_folder = os.path.dirname(output_path)
        if not os.path.isdir(output_folder):
            os.makedirs(output_folder)

        print("Downloading %s..." % output_path)
        self.fw.download_file_from_acquisition(acq_id, filename, output_path)


    """
    Project
    """
    def _find_project_label(self, session):
        project_id = session.project
        return self.fw.get_project(project_id).label


    """
    Subject
    """
    def _determine_subject(self, session):
        subject = session.subject.code
        subject = subject.lower()
        project = self._find_project_label(session)
        if subject.startswith("rad"):
            return subject.split("-")[0]
        elif subject.startswith("conn"):
            return subject.split("_")[0]
        elif project == "engage":
            return subject[:len("LA13012")]

    def _filter_subject(self, sessions, subject):
        subject = subject.lower()
        sessions = [s for s in sessions if self._determine_subject(s) == subject]
        return sessions


    """
    Time session
    """
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
        subject_id = session.subject.code.upper()
        if project == "engage":
            if subject_id.endswith("12MO"): # check before 2MO.  Be careful!
                return tag_map["12MO"]
            for tag in ("BV", "2MO", "6MO", "24MO"):
                if subject_id.endswith(tag):
                    return tag_map[tag]
            return "000_data_archive"
        elif project == "connectome":
            return self._fw_time_session(session.id)
        elif project == "rad":
            if "-" in subject_id:
                session_map = {"1": "000_data_archive", "2": "001_data_archive"}
                session = subject_id.split("-")[1]
                return session_map[session]
        raise Exception("Project %s not known" % project)

    def _fw_time_session(self, session_id):
        """
        It's very important to get the tags from this method.  If you pass in a session from
        fw.get_project_sessions, the tags don't show up for some reason.
        """
        possible_sessions = {"3MO", "6MO", "12MO", "24MO"}
        tags = self.fw.get_session(session_id).tags
        tags = set(tags)
        time_session = tags.intersection(possible_sessions)
        if len(time_session) == 0:
            return "000_data_archive"
        elif len(time_session) > 1:
            raise Exception("Multiple time sessions (%s) for session ID %s." % (", ".join(list(time_session)), session_id))
        else:
            return "%s_data_archive" % (time_session.pop())

    def _filter_time_session(self, sessions, time_session):
        sessions = [s for s in sessions if self._determine_time_session(s) == time_session]
        return sessions


    """
    Tasks
    """
    def _get_task_files(self, sessions, task_name):
        task_files = list()
        for session in sessions:
            for acq in self.fw.get_session_acquisitions(session.id):
                if self._is_match(acq.label, task_name):
                    task_files.append(acq.id)
        return task_files

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
        elif task_name == "rs1_pe0" and ("rsfmri" in fw_label and "_1_pe0" in fw_label):
            return True
        elif task_name == "rs1_pe1" and ("rsfmri" in fw_label and "_1_pe1" in fw_label):
            return True
        elif task_name == "rs2_pe0" and ("rsfmri" in fw_label and "_2_pe0" in fw_label):
            return True
        elif task_name == "rs2_pe1" and ("rsfmri" in fw_label and "_2_pe1" in fw_label):
            return True
        elif task_name == "mid" and "tfmri_mid" in fw_label:
            return True
        elif task_name == "emotion" and "tfmri_emotion" in fw_label:
            return True
        elif task_name == "wm" and "tfmri_wm" in fw_label:
            return True
        elif task_name == "gambling" and "tfmri_gambling" in fw_label:
            return True
        return False

    def _get_dicom_filename(self, acq_id):
        acq = self.fw.get_acquisition(acq_id)
        dicom = [f.name for f in acq.files if f.name.endswith(".dicom.zip")]
        assert len(dicom) == 1, "Multiple dicoms found"
        return dicom.pop()

