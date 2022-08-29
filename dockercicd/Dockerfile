FROM ubuntu:22.04
LABEL maintainer='Mario David <mariojmdavid@gmail.com>'

RUN apt-get update && apt-get install -y --no-install-recommends \
        apt-utils \
        cmake \
        curl \
        gcc \
        git \
        libcurl4 \
        libcurl4-openssl-dev \
        libpython3-dev \
        libssl-dev \
        libyaml-dev \
        locales \
        make \
        openssh-server \
        pkg-config \
        procps \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python-is-python3 \
        ruby-dev \
        ruby-rubygems \
        sudo \
        vim \
        wget && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install pycurl wheel watchdog coverage twine \
                pytest pytest-runner pylint pydocstyle nose nosexcover \
                mock pep8 bandit GitPython PyGithub python-gitlab

RUN gem install mdl licensee

COPY checkCitable.py /usr/bin/checkCitable.py
COPY get_git_tags.py /usr/bin/get_git_tags.py
RUN chmod +x /usr/bin/get_git_tags.py /usr/bin/checkCitable.py
