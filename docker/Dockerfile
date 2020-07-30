FROM jupyter/scipy-notebook
LABEL maintainer="iwasakishuto <cabernet.rock@gmail.com>"

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
    pip install \
      beautifulsoup4>=4.9.1 \
      jinja2>=2.11.2 \
      lxml>=4.5.1 \
      nltk>=3.5 \
      pdfkit>=0.6.1 \
      pdfminer \
      pylatexenc>=2.5 \
      python-dotenv>=0.13.0 \
      python-magic>=0.4.18 \
      requests>=2.24.0 \
      selenium>=3.141.0 && \
      git clone git://github.com/julian-r/python-magic.git /src2 && pip install -e /src2 && \
      git clone git://github.com/iwasakishuto/Translation-Gummy.git /src && pip install -e /src[tests] && \
      pip install git+git://github.com/iwasakishuto/Translation-Gummy.git

ENV PYTHONPATH='/src/:$PYTHONPATH'

WORKDIR /data

CMD jupyter notebook --port=8888 --ip=0.0.0.0