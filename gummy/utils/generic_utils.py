# coding: utf-8
import os
import re
import shutil
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


def handleKeyError(lst, **kwargs):
    k,v = kwargs.popitem()
    if v not in lst:
        lst = ', '.join([f"'{e}'" for e in lst])
        raise KeyError(f"Please choose the argment {toBLUE(k)} from {lst}. you chose {toRED(v)}")

def handleTypeError(types, **kwargs):
    type2str = lambda t: re.sub(r"<class '(.*?)'>", r"\033[34m\1\033[0m", str(t))
    k,v = kwargs.popitem()
    if not any([isinstance(v,t) for t in types]):
        str_true_types  = ', '.join([type2str(t) for t in types])
        srt_false_type = type2str(type(v))
        if len(types)==1:
            err_msg = f"must be {str_true_types}"
        else:
            err_msg = f"must be one of {str_true_types}"
        raise TypeError(f"{toBLUE(k)} {err_msg}, not {toRED(srt_false_type)}")

def mk_class_get(all_classes={}, gummy_abst_class=[], genre=""):
    if not isinstance(gummy_abst_class, list):
        gummy_abst_class = [gummy_abst_class]
    def get(identifier, **kwargs):
        if isinstance(identifier, str):
            identifier = identifier.lower()
            handleKeyError(lst=list(all_classes.keys()), identifier=identifier)
            instance = all_classes.get(identifier)(**kwargs)
        else:
            handleTypeError(types=[str] + gummy_abst_class, identifier=identifier)
            instance = identifier
        return instance
    get.__doc__ = f"""
    Retrieves a Translation-Gummy {genre.capitalize()} instance.
    @params identifier : {genre.capitalize()} identifier, string name of a {genre}, or
                         a Translation-Gummy {genre.capitalize()} instance.
    @params kwargs     : parametes for class initialization.
    @return {genre:<11}: A Translation-Gummy{genre.capitalize()} instance.
    """
    return get

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

def readable_size(size):
    for unit in ['K','M','G']:
        if abs(size) < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f} [{unit}B]"

def splitted_query_generator(query, maxsize=5000):
    """ Use 'Natural Language Toolkit (https://www.nltk.org/index.html)' to split text wisely.
    @params query   : (str) English texts.
    @params maxsize : (int) Number of English characters that this generator can yield at one time.
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

class MonoParamProcessor(argparse.Action):
    """
    Receive an argument as a dictionary.
    =====================================================
    (sample)
    $ python argparse_handler.py --dict_param foo=a --dict_param bar=b
    >>> {'foo': 'a', 'bar': 'b'}
    """
    def __call__(self, parser, namespace, values, option_strings=None):
        param_dict = getattr(namespace,self.dest,[])
        if param_dict is None:
            param_dict = {}

        k, v = values.split("=")
        param_dict[k] = v
        setattr(namespace, self.dest, param_dict)