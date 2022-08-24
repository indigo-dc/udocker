FROM ubuntu:22.04
LABEL maintainer='Mario David <mariojmdavid@gmail.com>'

RUN apt update && apt install -y --no-install-recommends \
        git \
        curl \
        libcurl4 \
        libcurl4-openssl-dev \
        libpython3-dev \
        libssl-dev \
        vim \
        procps \
        gcc \
        python3-dev \
        libyaml-dev \
        python3-setuptools \
        python3-pip \
        python3-wheel \
        python-is-python3 \
        wget && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

COPY ../requirements-dev.txt /tmp/requirements-dev.txt
RUN pip install -r /tmp/requirements-dev.txt
