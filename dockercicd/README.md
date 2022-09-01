# Dockerfile for CI/CD

This directory container the Dockerfile to run the Jenkins CI/CD pipeline of udocker.

Local build the docker image:

```bash
docker build -t udockercicd .
```

To create the containers for the tests of CI/CD locally, execute from the repository directory:

```bash
docker-compose -f .sqa/docker-compose.yml --project-directory . up -d
```

Run CI/CD test of the pipeline:

```bash
docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.acc_udocker \
    git rev-parse --is-inside-work-tree

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.doc_udocker \
    mdl -r ~MD013,~MD029 .

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.lic_udocker \
    licensee detect .

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.met01_udocker \
    python /usr/bin/checkCitable.py https://github.com/indigo-dc/udocker

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.met02_udocker \
    cat codemeta.json

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.sec_udocker \
    bandit -f html -o bandit.html udocker

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.sty_udocker \
    pylint --rcfile=pylintrc udocker

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.uni_udocker \
    nosetests -v --with-xcoverage --cover-package=udocker tests/unit/test*.py

docker-compose -f .sqa/docker-compose.yml --project-directory . exec qc.ver_udocker \
    python /usr/bin/get_git_tags.py --repo-path ./
```
