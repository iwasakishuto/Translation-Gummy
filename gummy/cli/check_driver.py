# coding: utf-8
"""CLI(Command Line Interface) tools

    Check whether you can use the installed driver and find out the cause of the error.
"""
import argparse
import imp
import sys

from ..utils.coloring_utils import toGREEN
from ..utils.driver_utils import DRIVER_TYPE, SUPPORTED_DRIVER_TYPES, get_driver


def check_driver(argv=sys.argv[1:]):
    """Translate journals.

    Args:
        driver-type (str) : The type of driver you want to find out.

    Note:
        When you run from the command line, execute as follows::

        $ gummy-driver -T local
        $ gummy-driver -T remote

    """
    parser = argparse.ArgumentParser(prog="gummy-driver", add_help=True)
    parser.add_argument(
        "-T",
        "--driver-type",
        type=str,
        default=DRIVER_TYPE,
        choices=SUPPORTED_DRIVER_TYPES,
        help="URL of a page you want to create a pdf.",
    )
    args = parser.parse_args(argv)

    driver = get_driver(driver_type=args.driver_type)
    print(toGREEN("If you see this message, it's OK :)"))
