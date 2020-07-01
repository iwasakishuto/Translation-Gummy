# pytest

- doc: [https://docs.pytest.org/](https://docs.pytest.org/)

## Installation

```sh
$ pip install pytest
$ pytest --version   # shows where pytest was imported from
$ pytest --fixtures  # show available builtin function arguments
$ pytest -h | --help # show help on command line and config file options
```

## Usage

If you want to know the default options, see [`pytest.ini`](https://github.com/iwasakishuto/Translation-Gummy/blob/master/pytest.ini)

- Run all tests:
    ```sh
    $ pytest
    ```
- Specifying tests / selecting tests:
    ```sh
    # Run tests in a module
    $ pytest test_mod.py
    # Run tests in a directory
    $ pytest testing/
    ```
- Profiling test execution duration
    ```sh
    $ pytest --durations=10
    ```
- Stopping after the first (or N) failures:
    ```sh
    # stop after first failure
    $ pytest -x
    # stop after two failures
    $ pytest --maxfail=2
    ```

## Create All test programs

Detect program files which don't have test programs (`test_....py`) in this directory.

```sh
$ python _generate_all_templates.py
```