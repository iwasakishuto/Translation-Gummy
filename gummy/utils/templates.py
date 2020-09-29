#coding: utf-8
"""This program file is only for `documents <https://iwasakishuto.github.io/Translation-Gummy/index.html>`_. 
You can see the same contents by looking at `Github <https://github.com/iwasakishuto/Translation-Gummy/tree/master/gummy/templates>`_ .
"""
import os
from gummy.utils import TEMPLATES_DIR

def _mk_func(fn):  
    fp = os.path.join(TEMPLATES_DIR, fn)
    with open(fp, mode="r") as f:
        code = "\t".join(f.readlines())
    def func():
        return fp
    func.__doc__ = f"""Return ``TEMPLATES_DIR``/{fn}
    
    Returns:
        str : Where this file is.

    The contents of the file are as follows:

    .. code-block:: html
        
        {code}
    """
    return func

for fn in os.listdir(TEMPLATES_DIR):
    if fn[-5:] != ".html": continue
    name = fn.replace(".", "_")
    exec(f"{name} = _mk_func('{fn}')")
