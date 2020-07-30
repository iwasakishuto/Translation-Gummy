# Using Translation-Gummy via Docker

This directory contains `Dockerfile` to make it easy to get up and running with Translation-Gummy via [Docker](http://www.docker.com/).

## Installing Docker

General installation instructions are [on the Docker site](https://docs.docker.com/installation/), but we give some quick links here:

- [OSX](https://docs.docker.com/installation/mac/): [docker toolbox](https://www.docker.com/toolbox)
- [ubuntu](https://docs.docker.com/installation/ubuntulinux/)

## Running the container

We are using `Makefile` to simplify docker commands within make commands.

Build the container and start a Jupyter Notebook

```sh
$ make notebook
```

Build the container and mount [`examples`](https://nbviewer.jupyter.org/github/iwasakishuto/Translation-Gummy/blob/master/examples/), then start a Jupyter Notebook

```sh
$ make examples
```

Build the container and start an iPython shell

```sh
$ make ipython
```

Build the container and start a bash

```sh
$ make bash
```

Mount a volume for external data sets

```sh
$ make DATA=~/mydata
```

Prints all make tasks

```sh
$ make help
```