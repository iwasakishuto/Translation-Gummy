FROM jupyter/scipy-notebook
LABEL maintainer="iwasakishuto <cabernet.rock@gmail.com>"
ARG requirements="Translation-Gummy"

USER root
# Install system packages

RUN echo "deb http://security.ubuntu.com/ubuntu bionic-security main" >> /etc/apt/sources.list \
 && apt-get update --fix-missing \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends \
      vim \
      cmake \
      g++ \
      git \
    #   wkhtmltopdf 
      build-essential \
      xorg \
    #   libssl-dev \
      libssl1.0-dev \      
      libxrender-dev \
      unzip \
      gdebi \
      wget \
      xvfb \
      libfontconfig \
 && apt-get autoremove -y \
 && apt-get clean -y \
 && rm -rf /var/lib/apt/lists/*

# Copy or Download Japanese fonts.
COPY fonts /usr/share/fonts
RUN if [ "$(ls -U1 /usr/share/fonts | wc -l)" -gt 0 ]; then \
      echo "Use the font you have prepared:\n$(ls fonts)"; \
    else \
      echo "Download Japanese fonts"; \
      wget https://noto-website.storage.googleapis.com/pkgs/Noto-unhinted.zip \
        && unzip -d NotoSansJapanese Noto-unhinted.zip \
        && mkdir -p /usr/share/fonts/opentype \
        && mv -fv ./NotoSansJapanese /usr/share/fonts/opentype/NotoSansJapanese \
        && rm -rfv Noto-unhinted.zip \
        && fc-cache -fv; \
    fi

# Set locale.
RUN apt-get install -y locales \
  && locale-gen ja_JP.UTF-8 \
  && localedef -f UTF-8 -i ja_JP ja_JP
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:jp
ENV LC_ALL ja_JP.UTF-8

# Install wkhtmltopdf. (with patched qt)
WORKDIR /opt
ENV WKHTMLTOPDF_VERSION 0.12.4
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/${WKHTMLTOPDF_VERSION}/wkhtmltox-${WKHTMLTOPDF_VERSION}_linux-generic-amd64.tar.xz
RUN tar vxfJ wkhtmltox-${WKHTMLTOPDF_VERSION}_linux-generic-amd64.tar.xz \
 && ln -s /opt/wkhtmltox/bin/wkhtmltopdf /usr/bin/wkhtmltopdf

# Permission.
ENV NB_USER gummy
ENV NB_UID 1001
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    mkdir -p /src /src-python-magic && \
    chown $NB_USER /src /src-python-magic
USER $NB_USER
 
# Install Python packages and PyGuitar
RUN pip install --upgrade pip && \
    pip install ${requirements} && \
    git clone git://github.com/julian-r/python-magic.git /src-python-magic && pip install -e /src-python-magic && \
    git clone git://github.com/iwasakishuto/Translation-Gummy.git /src && pip install -e /src[tests] && \
    pip install git+git://github.com/iwasakishuto/Translation-Gummy.git

ENV PYTHONPATH='/src/:$PYTHONPATH'

WORKDIR /data

CMD jupyter notebook --port=8888 --ip=0.0.0.0