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
