# coding: utf-8
import os
import shutil
try:
    from nltk.tokenize import sent_tokenize, word_tokenize
except LookupError:
    print("You have to download some functions for using NLTK.")
    import nltk
    nltk.download('punkt')
    from nltk.tokenize import sent_tokenize, word_tokenize

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