# Using Translation-Gummy via Docker (Docker Compose)

This directory contains `docker-compose.yml` and environment files (stored at `env/`) to make it easy to get up and running with Translation-Gummy via [Docker Compose](https://docs.docker.com/compose/).

## Installing Docker Compose

General installation instructions are [on the Docker site](https://docs.docker.com/compose/install/).

## Store Fonts

```sh
# Open these directory and Copy your favorite font to 'fonts' dir.
$ open /System/Library/Fonts
$ open /Library/Fonts
$ open $HOME/Library/Fonts
$ copy /path/to/font.ttf[ttc] fonts/
```

## Running the container

I prepare `Makefile` to simplify `docker-compose` commands within make commands.

- Build the container and translate journal.
    ```sh
    $ make bash
    (docker)> gummy-journal "https://www.nature.com/articles/ncb0800_500" \
                                            -G "useless" \
                                            -T "deepl" \
                                            -O .
    ```
- Build the container and start a Jupyter Notebook.
    ```sh
    $ make notebook
    ```
- Build the container and mount [`examples`](https://nbviewer.jupyter.org/github/iwasakishuto/Translation-Gummy/blob/master/examples/), then start a Jupyter Notebook.
    ```sh
    $ make examples
    ```
- Build the container and start an iPython shell.
    ```sh
    $ make ipython
    ```
- Build the container and start a bash.
    ```sh
    $ make bash
    ```
- Mount a volume for external data sets.
    ```sh
    $ make DATA=~/mydata
    ```
- Prints all make tasks.
    ```sh
    $ make help
    ```