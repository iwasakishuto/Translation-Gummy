#coding: utf-8
""" Utility programs for handling compression and decompression """
import os
import shutil
import bz2
import gzip
import zipfile
import tarfile
import mimetypes
from abc import ABCMeta, abstractstaticmethod

from .coloring_utils import toBLUE, toRED
from .generic_utils import recreate_dir

def get_mimetype_mimetypes(path):
    """Guess the type of a file based on its URL (filename).

    Args:
        path (str) : filename
    
    Returns:
        - ``None`` (if the type can't be guessed (no or unknown suffix)
        -  a string of the form ``type/subtype`` (otherwise)

    Examples:
        >>> get_mimetype_mimetypes("gummy.zip")
        'application/zip'
        >>> get_mimetype_mimetypes("gummy.tar.gz")
        'application/x-tar'
        # Check the difference when `path` does not exist.
        >>> os.path.exists("gummy.png")
        True
        >>> get_mimetype_mimetypes("gummy.png")
        'image/png'
        >>> os.path.exists("gummy_.png")
        False
        >>> get_mimetype_mimetypes("gummy_.png")
        'image/png'
    """
    return mimetypes.guess_type(path)[0]

def get_mimetype_libmagic(path):
    """Accepts a filename and returns the detected filetype.
    
    Args:
        path (str) : filename

    Returns:
        str : 
            - ``None`` (if the file does not exist)
            -  a string of the form ``type/subtype`` (otherwise)
    
    Examples:
        >>> get_mimetype_libmagic("gummy.zip")
        'application/zip'
        >>> get_mimetype_libmagic("gummy.tar.gz")
        'application/x-tar'
        # Check the difference when `path` does not exist.
        >>> os.path.exists("gummy.png")
        True
        >>> get_mimetype_libmagic("gummy.png")
        'image/png'
        >>> os.path.exists("gummy_.png")
        False
        >>> print(get_mimetype_mimetypes("gummy_.png"))
        None
    """
    return magic.from_file(path, mime=True) if os.path.exists(path) else None

try:
    import magic
    get_mimetype = get_mimetype_libmagic
except ImportError:
    print(f"failed to find {toBLUE('libmagic')}, so use {toBLUE('mimetypes')} instead.")
    get_mimetype = get_mimetype_mimetypes

def is_compressed(ext):
    """Check whether file is compressed or not from the extensions."""
    return ext in [".zip", ".gz", ".tar.gz", ".tgz", "bzip2", ".tar.bz2", ".tar"]

def extract_from_compressed(path, ext=None, dirname=".", verbose=True):
    """Extract files from compressed file.

    Args:
        path (str)      : path/to/compressed_file.
        ext (str)       : Extract only files with this extension from compressed files. If ``None``, all files will be extracted.
        dirname (str)   : Where the extracted file will be stored.
        verbose (bool)  : Whether print names in extracted file or not.

    Returns:
        list : Paths of extracted files.
    """
    zip_ext = os.path.splitext(path)[-1]
    if zip_ext == "":
        mimetype = get_mimetype(path)
        zip_ext = ".zip" if (mimetype is not None) and (mimetype.split("/")[-1] == "zip") else None
    Extractor = {
        ".zip" : ZipExtractor
    }.get(zip_ext, TarExtractor)
    extracted_file_paths = Extractor.extract_from_compressed(
        path=path, ext=ext, dirname=dirname, verbose=verbose,
    )
    return extracted_file_paths

class GummyAbstExtractor(metaclass=ABCMeta):
    """File Extractor."""
    @classmethod
    def extract_from_compressed(cls, path, ext=None, dirname=".", verbose=True):
        """Extract files from compressed file.

        Args:
            path (str)      : path/to/compressed_file.
            ext (str)       : Extract only files with this extension from compressed files. If ``None``, all files will be extracted.
            dirname (str)   : Where the extracted file will be stored.
            verbose (bool)  : Whether print names in extracted file or not.

        Returns:
            list : Paths of extracted files.
        """
        extracted_file_paths = []
        print(f"Contents in {toBLUE(path)}:")
        with cls.open_compressed_file(path) as compressed_f:
            for name in cls.get_namelist(compressed_f):
                if ext is None or name.endswith(ext):
                    compressed_f.extract(name, path=dirname)
                    extracted_file_path = os.path.join(dirname, name)
                    extracted_file_paths.append(extracted_file_path)
                    name += f" (Save at {toBLUE(extracted_file_path)})"
                if verbose: print(f"\t- {name}")
        return extracted_file_paths

    @abstractstaticmethod
    def open_compressed_file(path):
        """Open a compressed file."""
        return open(path)

    @abstractstaticmethod
    def get_namelist(compressed_f):
        """Get name list in the extracted file."""
        for name in compressed_f.namelist():
            yield name
            
class ZipExtractor(GummyAbstExtractor):
    """Extractor for Zip file.

    .. code-block:: python

        >>> import zipfile
        >>> with zipfile.ZipFile(path) as f:
        ...     for name in f.get_namelist():
        ...         print(name)
    """
    @staticmethod
    def open_compressed_file(path):
        return zipfile.ZipFile(path)
    
    @staticmethod
    def get_namelist(compressed_f):
        for name in compressed_f.namelist():
            yield name
            
class TarExtractor(GummyAbstExtractor):
    """Extractor for Tar file.
    
    .. code-block:: python

        >>> import tarfile
        >>> with tarfile.open(path) as f:
        ...     for m in f.getmembers():
        ...         name = m.name
        ...         print(name)
    """
    @staticmethod
    def open_compressed_file(path):
        return tarfile.open(path)
    
    @staticmethod
    def get_namelist(compressed_f):
        for m in compressed_f.getmembers():
            name = m.name
            yield name