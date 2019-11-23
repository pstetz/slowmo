import os
from tqdm import tqdm
from glob import glob
from os.path import join
from log_parser import log_parser
from txt_parser import txt_parser

def _task_map():
    _map = {
        "101_fMRI_preproc_GO_NO_GO": "gonogo",
        "104_fMRI_preproc_WORKING_MEMORY": "workingmemSB",
        "103_fMRI_preproc_FACES-CONSCIOUS": "conscious",
        "105_fMRI_preproc_FACES-NONCONSCIOUS": "nonconscious",
        "1011_fMRI_preproc_EMO_CONFLICT": "emoconflict",
        "1026_fMRI_preproc_WORKING_MEMORY": "workingmemMB",
    }
    return _map


def _project_map():
    _map = {
        "connhc": "CONNECTOME/conn_hc/dof-12",
        "connmdd": "CONNECTOME/conn_mdd/dof-12",
        "engage": "ENGAGE",
        "engage2": "ENGAGE_2",
        "rad": "RAD",
    }
    return _map

def determine_subject_num(subject, task_path):
    subject_num = ""
    for i in range(1, len(subject)):
        if subject[-i:].isdigit():
            subject_num = subject[-i:]
        else:
            break
    if not subject_num:
        raise Exception("Cannot determine subject num from %s in %s" % (subject, task_path))
    subject_num = "%08d" % int(subject_num)
    return subject_num

def _find_txt(task_path, subject, task):
    subject_num = determine_subject_num(subject, task_path)
    legacy_task_map = {
            "gonogo": "GoNoGo",
            "conscious": "EmotionConscious",
            "nonconscious": "EmotionNonconscious",
            "workingmemSB": "WorkingMemory",
            "emoconflict": "EmotionalStroopTask",
    }
    if task not in legacy_task_map:
        return False
    legacy_task = legacy_task_map[task]
    txt_file = glob(join(task_path, "%s*%s*.txt" % (subject_num, legacy_task)))
    return _safe_log_pop(txt_file, task_path, ".txt")

def _safe_log_pop(log_results, task_path, ext):
    if len(log_results) > 1:
        raise Exception("Found multiple %s log files for %s" % (ext, task_path))
    if len(log_results) == 0:
        return False
    return log_results.pop()

def _find_log(task_path, subject, task):
    subject = subject.upper()
    current_task_map = {
            "gonogo": "GoNoGo",
            "conscious": "Faces Conscious",
            "nonconscious": "Faces Nonconscious",
            "workingmemMB": "WorkingMemMultiband",
    }
    if task not in current_task_map:
        return False
    current_task = current_task_map[task]
    log_file = glob(join(task_path, "%s*%s*.log" % (subject.upper(), current_task)))
    return _safe_log_pop(log_file, task_path, ".log")

def create_onsets(task_path, subject, task, dst_path):
    txt = _find_txt(task_path, subject, task)
    log = _find_log(task_path, subject, task)
    if txt and log:
        msg = "Found two possible log files for %s" % task_path
        raise Exception(msg)
    elif txt:
        txt_parser(txt, dst_path, task)
    elif log:
        log_parser(log, dst_path, task)
    else:
        return

def _dst_path(output_, time_session, subject, task):
    session = time_session.replace("_data_archive", "")
    subject = subject.lower().replace("-", "").replace("_", "")
    return join(output_, session, subject, task, "onsets.csv")

def gather_and_parse(input_, output_):
    for subject_path in tqdm(glob(join(input_, "*"))):
        subject = os.path.basename(subject_path)
        for time_path in glob(join(subject_path, "*")):
            time_session = os.path.basename(time_path)
            for plip_task in _task_map().keys():
                task = _task_map()[plip_task]
                task_path = join(time_path, "100_fMRI", plip_task)
                if not os.path.isdir(task_path):
                    continue
                dst_path = _dst_path(output_, time_session, subject, task)
                if os.path.isfile(dst_path):
                    # print("Onsets already created for %s" % task_path)
                    continue
                dst_folder = os.path.dirname(dst_path)
                if not os.path.isdir(dst_folder):
                    os.makedirs(dst_folder)
                try:
                    create_onsets(task_path, subject, task, dst_path)
                except:
                    print(task_path)

if __name__ == "__main__":
    root = "/Volumes/group/PANLab_Datasets"
    dst  = "/Volumes/hd_4tb/raw"
    projects = ["connhc", "connmdd", "engage", "engage2", "rad"]

    for project in projects:
        project_root = join(root, _project_map()[project])
        input_       = join(project_root, "data")
        output_      = join(dst, project)

        gather_and_parse(input_, output_)

