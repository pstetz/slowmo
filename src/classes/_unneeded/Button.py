import os
from glob import glob
from os.path import join

class Button:

    def __init__(self, project, subject, time_session, task):
        self.project = project
        self.subject = subject
        self.time_session = time_session
        self.task = task

    def _get_button_folder(self):
        data_root = "/Volumes/group/PANLab_Datasets"
        study_path_map = {
            "RAD": join(data_root, "RAD_Button_Response_Folder"),
            "ENGAGE": join(data_root, "ENGAGE", "button"),
            "ENGAGE_2": join(data_root, "ENGAGE_2", "button"),
            "CONNECTOME": join(data_root, "Conn_Button_Response_Folder"),
        }
        assert self.project in button_loc, "Project %s does not have a button folder" % self.project
        return study_path_map[study]

    def find_logfile(self):
        button_folder = self._get_button_folder()
        subject_folder = self._button_subject_folder()
        filename = self._button_filename(subject_folder)
        search = join(button_folder, subject_folder, filename)
        possible_matches = glob(search)
        assert len(possible_matches) != 0, "No matches found for %s" % search
        assert len(possible_matches) == 1, "Multiple matches found for %s" % search
        return possible_matches.pop()

    def _button_filename(self, subject_folder):
        if self.project == "engage":
            return self_engage_filename(subject_folder)
        elif self.project == "rad":
            pass
        elif self.project == "connectome":
            return
        msg = "No function to determine button for project %s" % self.project
        raise Exception(msg)

    def _engage_filename(self, subject_folder):
        """
        FIXME: This type of filename needs to be included too
        /00022728/00022728_s5_Faces Nonconscious_2018_Oct_11_1328.log
        """
        session_number = {
                "000_data_archive": "1",
                "2MO_data_archive": "2",
                "6MO_data_archive": "3",
                "12MO_data_archive": "4",
                "24MO_data_archive": "5"
                }[self.time_session]
        task_name = {
                "gonogo": "GoNoGo",
                "conscious": "EmotionConscious",
                "nonconscious": "EmotionNonconscious"
                }[self.task]
        return "%s-%s_%s*" % (subject_folder, session_number, task_name)

    def _button_subject_folder(self):
        if self.project == "connectome":
            return self.subject.upper()
        if self.project == "engage":
            return self.subject[2:].rjust(8, "0")

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

