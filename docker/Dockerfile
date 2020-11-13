FROM jupyter/scipy-notebook
LABEL maintainer="iwasakishuto <cabernet.rock@gmail.com>"
ARG requirements="Translation-Gummy"

USER root
# Install system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      vim \
      bzip2 \
      cmake \
      g++ \
      git \
      graphviz \
      libgl1-mesa-glx \
      libhdf5-dev \
      openmpi-bin \
      wget \
      xvfb \
      libfontconfig \
      wkhtmltopdf && \
    rm -rf /var/lib/apt/lists/*

# Permission.
ENV NB_USER gummy
ENV NB_UID 1001
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    mkdir -p /src /src2 && \
    chown $NB_USER /src /src2
USER $NB_USER
 
# Install Python packages and PyGuitar
RUN pip install --upgrade pip && \
    pip install ${requirements} && \
    git clone git://github.com/julian-r/python-magic.git /src2 && pip install -e /src2 && \
    git clone git://github.com/iwasakishuto/Translation-Gummy.git /src && pip install -e /src[tests] && \
    pip install git+git://github.com/iwasakishuto/Translation-Gummy.git

ENV PYTHONPATH='/src/:$PYTHONPATH'

WORKDIR /data

CMD jupyter notebook --port=8888 --ip=0.0.0.0