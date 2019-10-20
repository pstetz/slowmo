"""
Imports
"""
import os
import gzip
import shutil
import nibabel as nib
from glob import glob
from tqdm import tqdm
from os.path import join


"""
Main
"""
def transfer(project, src_folder, dst_folder):
    for subject_path in tqdm(glob( join(src_folder, "data", "*") )):
        subject = os.path.basename(subject_path)

        for subject_time_path in glob( join(subject_path, "*") ):
            time_session = os.path.basename(subject_time_path)

            ### Transfer structural
            for struct, name in [
                    ("FSL_segmentation/w_FSL_greymatter_mask", "gm_probseg"),
                    ("reg/highres2standard_warp", "subject_to_MNI_warp"),
            ]:
                src = join(subject_time_path, "200_sMRI/003_FSL_fineFNIRT", struct)
                src = _prefer_compressed(src)
                if src:
                    dst = _determine_dst(dst_folder, project, subject, time_session, "structural", filename=name)
                    _safe_copy(src, dst)

            ### Transfer functionals
            for task_path in glob( join(subject_time_path, "100_fMRI", "10*") ):
                task_folder = os.path.basename(task_path)
                src = _plip_path(subject_time_path, task_folder, filename = "wa01_normalized_func_data")
                if src:
                    dst = _determine_dst(dst_folder, project, subject, time_session, task_folder)
                    _safe_copy(src, dst)

    return

def _safe_copy(src, dst):
    dst = _match_ext(dst, src)
    _copy(src, dst)
    _compress(dst)
    _uncompress(dst)

def _determine_dst(dst_folder, project, subject, time_session, folder, filename="normalized"):
    time    = time_session.replace("_data_archive", "")
    subject = subject.lower().replace("_", "").replace("-", "")
    if folder in _task_map():
        folder = _task_map()[folder]
    dst = join(dst_folder, project, time, subject, folder, filename)
    return dst


"""
PLIP specific
"""
def _task_map():
    task_map = {
            "101_fMRI_preproc_GO_NO_GO": "gonogo",
            "104_fMRI_preproc_WORKING_MEMORY": "workingmemSB",
            "103_fMRI_preproc_FACES-CONSCIOUS": "conscious",
            "105_fMRI_preproc_FACES-NONCONSCIOUS": "nonconscious",
            "1011_fMRI_preproc_EMO_CONFLICT": "emoconflict",
            "1012_fMRI_preproc_EMO_REG": "emoreg",
            "1026_fMRI_preproc_WORKING_MEMORY": "workingmemMB",
    }
    return task_map

def _plip_path(subject_time_folder, task_folder, filename = "wa01_normalized_func_data"):
    filepath = join(subject_time_folder, "100_fMRI", task_folder, filename)
    filepath = _prefer_compressed(filepath)
    return filepath


"""
File system
"""
def _prefer_compressed(filepath):
    for ext in (".nii.gz", ".nii", ".nii.tar.gz"):
        if os.path.isfile(filepath + ext):
            return filepath + ext
    return False

def _cut_ext(filepath):
    filename = os.path.basename(filepath)
    if "." in filename:
        parts = filename.split(".")
        name = parts[0]
        path = join(name, os.path.dirname(filepath))
        ext = "." + ".".join(parts[1:])
    else:
        path, ext = filepath, ""
    return path, ext

def _match_ext(path_1, path_2):
    path, _ = _cut_ext(path_1)
    _, ext  = _cut_ext(path_2)
    return path + ext

def _remove(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)

def _uncompress(compress_path):
    if not compress_path.endswith(".tar.gz"):
        return
    uncompress_path = compress_path.replace(".tar.gz", ".gz")
    _remove(uncompress_path)
    with tarfile.open(compress_path, "r:gz") as f_in:
        f_in.extractall()
        with gzip.open(uncompress_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(compress_path)

def _compress(uncompress_path):
    if uncompress_path.endswith(".gz"):
        return
    compress_path = uncompress_path + ".gz"
    _remove(compress_path)
    with open(uncompress_path, 'rb') as f_in:
        with gzip.open(compress_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(uncompress_path)

def _copy(src, dst):
    assert os.path.isfile(src), "%s not a file" % src
    if os.path.isfile(dst):
        # print("%s already exists.  Will not overwrite" % dst)
        return
    folder = os.path.dirname(dst)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    shutil.copy(src, dst)


"""
Read input arguments
"""
def _parse_args(args):
    if len(args) > 0:
        dst     = args.pop(-1)
        sources = args[:]
    else:
        root    = "/Volumes/group/PANLab_Datasets"
        sources = [
                ("connhc",  "CONNECTOME/conn_hc/dof-12"),
                ("connmdd", "CONNECTOME/conn_mdd/dof-12"),
                ("engage",  "ENGAGE"),
                ("engage2", "ENGAGE_2"),
                ("rad",     "RAD"),
                ]
        sources = [(project, join(root, path)) for project, path in sources]
        dst     = "/Volumes/hd_4tb/raw"
        print("No args provided using...\n\nsources: %s\ndst: %s\n" % (str(sources), dst))

    _validate(sources, dst)
    return sources, dst

def _validate(sources, dst):
    ### Correct type
    assert type(dst) == str, "dst %s should be a string" % str(dst)
    if type(sources) != list:
        msg = "src should be a list of src projects.  See type %s for %s" % (type(sources), str(sources))
        raise Exception(msg)

    ### Path exists
    assert os.path.isdir(dst), "dst %s does not exist" % dst
    for _, src in sources:
        assert os.path.isdir(src), "src %s does not exist" % src


"""
Main
"""
if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    sources, dst = _parse_args(args)
    for project, src in sources:
        print("Transferring %s..." % src)
        transfer(project, src, dst)
