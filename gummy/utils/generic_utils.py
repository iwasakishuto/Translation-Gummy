# coding: utf-8
""" Utility programs that can be used in general."""
import os
import re
import shutil
import datetime
import argparse
try:
    from nltk.tokenize import sent_tokenize, word_tokenize
    _ = sent_tokenize(text="gummy")
    _ = word_tokenize(text="gummy")
except LookupError:
    print("You have to download some resources for using NLTK.")
    import nltk
    nltk.download('punkt')
    from nltk.tokenize import sent_tokenize, word_tokenize

from .coloring_utils import toRED, toBLUE, toGREEN
from ._exceptions import KeyError

def handleKeyError(lst, **kwargs):
    """Check whether all ``kwargs.values()`` in the ``lst``.

    Args:
        lst (list) : candidates.
        kwargs     : ``key`` is the varname that is easy to understand when an error occurs

    Examples:
        >>> from pycharmers.utils import handleKeyError
        >>> handleKeyError(lst=range(3), val=1)
        >>> handleKeyError(lst=range(3), val=100)
        KeyError: Please choose the argment val from ['0', '1', '2']. you chose 100
        >>> handleKeyError(lst=range(3), val1=1, val2=2)
        >>> handleKeyError(lst=range(3), val1=1, val2=100)
        KeyError: Please choose the argment val2 from ['0', '1', '2']. you chose 100

    Raise:
        KeyError: If ``kwargs.values()`` not in the ``lst``
    """
    for k,v in kwargs.items():
        if v not in lst:
            lst = ', '.join([f"'{toGREEN(e)}'" for e in lst])
            raise KeyError(f"Please choose the argment {toBLUE(k)} from [{lst}]. you chose {toRED(v)}")

def class2str(class_):
    """Convert class to str.
    
    Args:
        class_ (class): class object
        
    Examples:
        >>> from pycharmers.utils import class2str
        >>> class2str(str)
        'str'
        >>> class2str(tuple)
        'tuple'

    """
    return re.sub(r"<class '(.*?)'>", r"\1", str(class_))

def handleTypeError(types, **kwargs):
    """Check whether all types of ``kwargs.values()`` match any of ``types``.

    Args:
        lst (list) : candidate types.
        kwargs     : ``key`` is the varname that is easy to understand when an error occurs

    Examples:
        >>> from pycharmers.utils import handleTypeError
        >>> handleTypeError(types=[str], val="foo")
        >>> handleTypeError(types=[str, int], val=1)
        >>> handleTypeError(types=[str, int], val=1.)
        TypeError: val must be one of ['str', 'int'], not float
        >>> handleTypeError(types=[str], val1="foo", val2="bar")
        >>> handleTypeError(types=[str, int], val1="foo", val2=1.)
        TypeError: val2 must be one of ['str', 'int'], not float

    Raise:
        TypeError: If the types of ``kwargs.values()`` are none of the ``types``
    """
    for k,v in kwargs.items():
        if not any([isinstance(v,t) for t in types]):
            str_true_types  = ', '.join([f"'{toGREEN(class2str(t))}'" for t in types])
            srt_false_type = class2str(type(v))
            if len(types)==1:
                err_msg = f"must be {str_true_types}"
            else:
                err_msg = f"must be one of [{str_true_types}]"
            raise TypeError(f"{toBLUE(k)} {err_msg}, not {toRED(srt_false_type)}")

def str_strip(string):
    """Convert all consecutive whitespace  characters to `' '` (half-width whitespace), then return a copy of the string with leading and trailing whitespace removed.

    Args:
        string (str) : string

    Example:
        >>> from pycharmers.utils import str_strip
        >>> str_strip(" hoge   ")
        'hoge'
        >>> str_strip(" ho    ge   ")
        'ho ge'
        >>> str_strip("  ho    g　e")
        'ho g e'
    """
    return re.sub(pattern=r"[\s 　]+", repl=" ", string=str(string)).strip()

def now_str(tz=None, fmt="%Y-%m-%d@%H.%M.%S"):
    """Returns new datetime string representing current time local to tz under the control of an explicit format string.

    Args:
        tz (datetime.timezone) : Timezone object. If no ``tz`` is specified, uses local timezone.
        fmt (str)              : format string. See `Python Documentation <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes>`_

    Example:
        >>> from pycharmers.utils import now_str
        >>> now_str()
        '2020-09-14@22.31.17'
        >>>now_str(fmt="%A, %d. %B %Y %I:%M%p")
        Monday, 14. September 2020 10:31PM'
        >>> now_str(tz=datetime.timezone.utc)
        '2020-09-14@13.31.17'
    """
    return datetime.datetime.now(tz=tz).strftime(fmt)

def mk_class_get(all_classes={}, gummy_abst_class=[], genre=""):
    """Create a get function.

    Args:
        all_classes (dict)      : Dictionary of ``identifier`` -> instance
        gummy_abst_class (list) : The list of GummyAbstClass names.
        genre (str)             : Genre of the class.
    """
    if not isinstance(gummy_abst_class, list): gummy_abst_class = [gummy_abst_class]
    gummy_abst_class = gummy_abst_class + [str]
    # Create a get function.
    def get(identifier, **kwargs):
        handleTypeError(types=gummy_abst_class, identifier=identifier)
        if isinstance(identifier, str):
            identifier = identifier.lower()
            handleKeyError(lst=list(all_classes.keys()), identifier=identifier)
            instance = all_classes.get(identifier)(**kwargs)
        else:
            instance = identifier
        return instance
    # Set a docstrings.
    genre = genre.capitalize()
    class_str = ", ".join([class2str(e) for e in gummy_abst_class])
    get.__doc__ = f"""Retrieves a Translation-Gummy {genre} instance.

    Args:
        identifier ({class_str}) : {genre} identifier, string name of a {genre}, or
                    {' '*len(class_str)}    a Translation-Gummy {genre} instance.

    Returns:
        {class2str(gummy_abst_class[0])} : A Translation-Gummy {genre} instance.
    """
    return get

def recreate_dir(path, exist_ok=True):
    """Super-mkdir. Create a leaf directory and all intermediate ones.

    Args:
        path (str)      : Path to the target directory.
        exist_ok (bool) : If the target directory already exists, raise an FileExistsError if ``exist_ok`` is ``False``.
    """
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

def readable_bytes(size):
    """Unit conversion for readability.
    Args:
        size (int): File size expressed in bytes

    Returns:
        tuple (int, str): (size, unit)

    Examples:
        >>> from pycharmers.utils import readable_bytes
        >>> size, unit = readable_bytes(1e2)
        >>> print(f"{size:.2f}[{unit}]")
        100.00[KB]
        >>> size, unit = readable_bytes(1e5)
        >>> print(f"{size:.2f}[{unit}]")
        97.66[MB]
        >>> size, unit = readable_bytes(1e10)
        >>> print(f"{size:.2f}[{unit}]")
        9.31[GB]
    """
    for unit in ["K","M","G"]:
        if abs(size) < 1024.0:
            break
        size /= 1024.0
        # size >> 10
    return (size, unit+"B")

def splitted_query_generator(query, maxsize=5000):
    """ Use `Natural Language Toolkit <https://www.nltk.org/index.html>`_ to split text wisely.

    NOTE: If ``word_tokenize(sentence) >> maxsize``, Get stuck in an infinite loop

    Args:
        query (str)   : English texts.
        maxsize (int) : Number of English characters that this generator can yield at one time.

    Examples:
        >>> from gummy.utils import splitted_query_generator
        >>> gen = splitted_query_generator(query="I have a pen. I have an apple. Apple pen! I have a pen. I have a pineapple. Pineapple pen! Applepen… pineapplepen… Pen-Pineapple-Apple-Pen! Pen-Pineapple-Apple-Pen!", maxsize=25)
        >>> for i,text in enumerate(gen):
        ...     print(i, text)
        0 I have a pen.
        1 I have an apple.
        2 Apple pen! I have a pen.
        3 I have a pineapple.
        4 Pineapple pen! Applepen…
        5 pineapplepen…
        6 Pen-Pineapple-Apple-Pen !
        7 Pen-Pineapple-Apple-Pen!
    """
    sent_tokenized_query = sent_tokenize(query)
    while True:
        splitted_query = ""
        num_allowed_chars = maxsize
        while len(sent_tokenized_query)>0:
            sentence = sent_tokenized_query.pop(0)
            len_sentence = len(sentence)
            if num_allowed_chars >= len_sentence:
                splitted_query += sentence + " "
                num_allowed_chars -= len_sentence+1
            else:
                # If the length of one sentence exceeds maxsize, split it into words.
                if len_sentence>maxsize:
                    sent_tokenized_query = word_tokenize(sentence) + sent_tokenized_query
                # Else, stop adding sentence and carry over the current one.
                else:
                    sent_tokenized_query.insert(0, sentence)
                    break
        if num_allowed_chars == maxsize:
            break
        else:
            yield splitted_query.rstrip(" ")

def get_latest_filename(dirname=".", ext=None):
    """Returns the most recently edited or added file path.
    
    Args:
        dirname (str) : Where the extracted file will be stored.
        ext (str)     : Extract only files with this extension from compressed files. If ``None``, all files will be extracted.

    Examples:
        >>> from gummy.utils import UTILS_DIR, get_latest_filename
        >>> get_latest_filename(UTILS_DIR)
        '/Users/iwasakishuto/Github/portfolio/Translation-Gummy/gummy/utils/__pycache__'
        >>> get_latest_filename(UTILS_DIR, ext=".py")
        '/Users/iwasakishuto/Github/portfolio/Translation-Gummy/gummy/utils/generic_utils.py'
    """
    if len(os.listdir(dirname)) == 0:
        return None
    else:
        return max([os.path.join(dirname,fn) for fn in os.listdir(dirname) if ext is None or fn.endswith(ext)], key=os.path.getctime)

class DictParamProcessor(argparse.Action):
    """Receive an argument as a dictionary.

    Raises:
        ValueError: You must give one argument for each one keyword.

    Examples:
        >>> import argparse
        >>> from gummy.utils import DictParamProcessor
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument("--dict_params", action=DictParamProcessor)
        >>> args = parser.parse_args(args=["--dict_params", "foo = [a, b, c]", "--dict_params", "bar=d"])
        >>> args.dict_params
        {'foo': ['a', 'b', 'c'], 'bar': 'd'}
        >>> args = parser.parse_args(args=["--dict_params", "foo=a, bar=b"])
        ValueError: too many values to unpack (expected 2)

    Note:
        If you run from the command line, execute as follows::
        
        $ python app.py --dict_params "foo = [a, b, c]" --dict_params bar=c

    """
    def __call__(self, parser, namespace, values, option_strings=None):
        param_dict = getattr(namespace, self.dest) or {}  
        k, v = values.split("=")
        match = re.match(pattern=r"\[(.+)\]", string=str_strip(v))
        if match is not None:
            v = [str_strip(e) for e in match.group(1).split(",")]
        else:
            v = str_strip(v)
        param_dict[str_strip(k)] = v
        setattr(namespace, self.dest, param_dict)

def try_wrapper(func, *args, ret_=None, msg_="", verbose_=True, **kwargs):
    """Wrap ``func(*args, **kwargs)`` with ``try-`` and ``except`` blocks.

    Args:
        func (functions) : functions.
        args (tuple)     : ``*args`` for ``func``.
        kwargs (kwargs)  : ``*kwargs`` for ``func``.
        ret_ (any)       : default ret val.
        msg_ (str)       : message to print.
        verbose_ (bool)  : Whether to print message or not. (default= ``True``) 
    
    Examples:
        >>> from gummy.utils import try_wrapper
        >>> ret = try_wrapper(lambda x,y: x/y, 1, 2, msg_="divide")
        Succeeded to divide
        >>> ret
        0.5
        >>> ret = try_wrapper(lambda x,y: x/y, 1, 0, msg_="divide")
        [division by zero] Failed to divide
        >>> ret is None
        True
        >>> ret = try_wrapper(lambda x,y: x/y, 1, 0, ret_=1, msg_="divide")
        >>> ret is None
        False
        >>> ret
        1
    """
    try:
        ret_ = func(*args, **kwargs)
        prefix = toGREEN("Succeeded to ")
    except Exception as e:
        prefix = toRED(f"[{str_strip(e)}] Failed to ")
    if verbose_: print(prefix + msg_)
    return ret_