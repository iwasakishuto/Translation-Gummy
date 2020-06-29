#coding: utf-8
import os
import shutil
import bz2
import gzip
import zipfile
import tarfile
from kerasy.utils import toBLUE, toRED

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

def extract_from_zip(zip_path, ext=".tex", dirname="."):
    with zipfile.ZipFile(zip_path) as zip_file:
        print(f"{toBLUE(zip_path)}'s contents:")
        print("="*30)
        extracted_file_paths = []
        for name in zip_file.namelist():
            if os.path.splitext(name)[1] == ext:
                zip_file.extract(name, path=dirname)
                extracted_file_path = os.path.join(dirname, name)
                extracted_file_paths.append(extracted_file_path)
                name += f" (Save at {toBLUE(extracted_file_path)})"
            print(f"- {name}")
    return extracted_file_paths

def extract_from_tar(tar_path, ext=".tex", dirname="."):
    unzipped_dir, tar_ext = os.path.splitext(tar_path)
    recreate_dir(unzipped_dir)
    with tarfile.open(tar_path) as tar_file:
        print(f"{toBLUE(tar_path)}'s contents:")
        print("="*30)
        print(f"- {unzipped_dir}/")
        extracted_file_paths = []
        dirname = os.path.join(dirname, unzipped_dir)
        for m in tar_file.getmembers():
            name = m.name
            if os.path.splitext(name)[1] == ext:
                tar_file.extract(name, path=dirname)
                extracted_file_path = os.path.join(dirname, name)
                extracted_file_paths.append(extracted_file_path)
                name += f" (Save at {toBLUE(extracted_file_path)})"
            print(f"- {name}")
    return extracted_file_paths

