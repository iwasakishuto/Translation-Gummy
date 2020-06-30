# coding: utf-8
import os
import shutil
from kerasy.utils import toRED, toGREEN

def recreate_dir(path, exist_ok=True):
    if os.path.exists(path):
        if exist_ok:
            if os.path.isdir(path):
                print(toRED("Delete existing directory"))
                shutil.rmtree(path)
            else:
                print(toRED("Delete existing file."))
                os.remove(path)
        else:
            raise FileExistsError(f"[Errno 17] File exists: '{path}'")
    os.makedirs(path, exist_ok=False)

def print_log(is_succeed, pos):
    if is_succeed:
        flag = toGREEN("[success]")
        content = "driver can be built."
    else:
        flag = toRED("[failure]")
        content = "driver can't be built."
    print(" ".join([flag, pos, content]))