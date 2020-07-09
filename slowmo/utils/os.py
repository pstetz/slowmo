import os
import shutil
from os.path import basename, dirname, isdir, isfile

def copy(src, dst):
    if not isdir(dirname(dst)):
        os.makedirs(dirname(dst))
    if isfile(dst):
        return
    shutil.copy(src, dst)
