# Dockerfiles with tools for SQAaaS

* Dockerfile-find_doc_files

```
docker build -t eoscsynergy/sqaaas-find_doc_files:1.0.0 -f Dockerfile-find_doc_files .
docker login docker.io
docker push eoscsynergy/sqaaas-find_doc_files:1.0.0
```

* Dockerfile-licensee

```
docker build -t eoscsynergy/sqaaas-licensee:1.0.0 -f Dockerfile-licensee .
docker login docker.io
docker push eoscsynergy/sqaaas-licensee:1.0.0
```

* Dockerfile-bandit

```
docker build -t eoscsynergy/sqaaas-bandit:1.0.1 -f Dockerfile-bandit .
docker login docker.io
docker push eoscsynergy/sqaaas-bandit:1.0.1
```

* Dockerfile-jsonlint

```
docker build -t eoscsynergy/sqaaas-jsonlint:1.0.0 -f Dockerfile-jsonlint .
docker login docker.io
docker push eoscsynergy/sqaaas-jsonlint:1.0.0
```

* Dockerfile-git_tags

```
docker build -t eoscsynergy/sqaaas-git_tags:1.0.0 -f Dockerfile-git_tags .
docker login docker.io
docker push eoscsynergy/sqaaas-git_tags:1.0.0
```

* Dockerfile-nosetests

```
docker build -t eoscsynergy/sqaaas-nosetests:1.0.0 -f Dockerfile-nosetests .
docker login docker.io
docker push eoscsynergy/sqaaas-nosetests:1.0.0
```
