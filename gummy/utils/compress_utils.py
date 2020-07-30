#coding: utf-8
import os
import shutil
import bz2
import gzip
import zipfile
import tarfile

from .coloring_utils import toBLUE, toRED
from .generic_utils import recreate_dir

try:
    import magic
    def get_mimetype(path):
        return magic.from_file(path, mime=True).split("/")[-1]
except ImportError:
    print(f"failed to find {toBLUE('libmagic')}, so use {toBLUE('mimetypes')} instead.")
    import mimetypes
    def get_mimetype(path):
        return mimetypes.guess_type(path)[0]

def is_compressed(ext):
    return ext in [".zip", ".gz", ".tar.gz", ".tgz", "bzip2", ".tar.bz2", ".tar"]

def extract_from_compressed(path, ext=".tex", dirname="."):
    zip_ext = os.path.splitext(path)[-1]
    if zip_ext == "":
        mimetype = get_mimetype(path)
        if mimetype == "zip":
            extract_func = extract_from_zip
        else:
            extract_func = extract_from_tar
    elif zip_ext == ".zip":
        extract_func = extract_from_zip
    else:
        extract_func = extract_from_tar
    return extract_func(path, ext=ext, dirname=dirname)
    
def extract_from_zip(zip_path, ext=".tex", dirname="."):
    with zipfile.ZipFile(zip_path) as zip_file:
        print(f"Contents in {toBLUE(zip_path)}:")
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
    unzipped_dir, _ = os.path.splitext(tar_path)
    recreate_dir(unzipped_dir)
    with tarfile.open(tar_path) as tar_file:
        print(f"Contents in {toBLUE(tar_path)}:")
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

