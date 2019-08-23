import os
import pandas as pd
from os.path import join
from datetime import datetime

class Logger:
    """
    ### Log
    Always starts a line with the current datetime
    Updates and error messages

    ### CSV
    This includes:
     - project, subject, time_session, task
     - Time of the model starting
     - Cost function
     - How long the model took to run
     - skip or not skip
     - num_iteration (how many times the model has iterated)
    """

    def __init__(self, log_path, csv_path):
        self.log_path = log_path
        self.csv_path = csv_path
        self.init_log()

    def init_log(self):
        pass

    def set(self,
            project=None, subject=None,
            time_session=None, task=None
            ):
        if project:
            self.project = project
        if subject:
            self.subject = subject
        if time_session:
            self.time_session = time_session
        if task:
            self.task = task

    def log(self, message, level=None):
        with open(self.log_path, "a") as f:
            pass

