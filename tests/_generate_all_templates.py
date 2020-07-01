# coding: utf-8
import os
from pathlib import Path

TESTS_DIR_PATH = os.path.dirname(os.path.abspath(__file__))              # path/to/tests
KERASY_LIB_PATH = os.path.join(os.path.dirname(TESTS_DIR_PATH), "gummy") # path/to/kerasy
STOP_FILE = ["__init__.py", "setup.py"] # Files which don't need test.
STOP_DIR = ["templates", "utils"] # Programs under these directories don't need test.

p = Path(KERASY_LIB_PATH)
for abs_path in p.glob("**/*.py"):
    rela_path = abs_path.relative_to(p)
    fn = rela_path.name       # hoge.py
    parent = rela_path.parent # (/path/to)/hoge.py

    # File Name check.
    if fn in STOP_FILE:
        continue

    # Directory name check.
    if any([par.name in STOP_DIR for par in rela_path.parents]):
        continue

    test_prog_path = os.path.join(parent, "test_" + fn)

    if not parent.exists():
        os.makedirs(parent)
        print(f"- [DIR] \033[32m{parent}\033[0m created.")

    if not os.path.exists(test_prog_path):
        with open(test_prog_path, mode="w") as f:
            f.write("# coding: utf-8")
        print(f"\t- [FILE] \033[34m{test_prog_path}\033[0m created.")