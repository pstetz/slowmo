import pandas as pd
from os.path import join

class Subject:
    def __init__(self, subject_id):
        self.subject = subject_id
        self._determine_project()

        df = self._get_df()
        self.get_age(df)
        self.get_sex(df)

    def _determine_project(self):
        subject = self.subject.lower()
        if subject.startswith("conn"):
            project = "connectome"
        elif subject.startswith("rad"):
            project = "rad"
        else:
            project = "engage"
        self.project = project
        return project

    def _get_df(self):
        data_root = "/Users/pbezuhov/git/MRI-SlowMo/data/project"
        csv_loc = {
              "rad": join(data_root, "rad", "rad.csv"),
              "engage": join(data_root, "engage", "engage.csv"),
              "connectome": join(data_root, "connectome", "connectome.csv"),
              }
        assert self.project in csv_loc, "Project %s does not have patient info" % self.project
        csv = csv_loc[self.project]
        return pd.read_csv(csv)

    def _get_subject(self, df):
        """ Returns a JSON of the subject information """
        subject = df[df["subject"] == self.subject]
        assert len(subject) != 0, "Subject %s not found" % self.subject
        assert len(subject) == 1, "Multiple subjects with id %s found" % self.subject
        info = subject.to_dict()
        print(info)
        info = {k: list(info[k].values()).pop() for k in info}
        return info

    def get_age(self, df):
        info = self._get_subject(df)
        age  = info["age"]
        self.age = age
        return age

    def get_sex(self, df):
        info = self._get_subject(df)
        sex  = info["gender"]
        self.sex = sex
        return sex

