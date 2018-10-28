#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library']) _

pipeline {
    agent {
        label 'python'
    }

    environment {
        dockerhub_repo = "indigodatacloud/udocker"
        tox_envs = """
[testenv:pylint]
commands = pylint --rcfile=pylintrc --disable=R,C udocker
[testenv:cobertura]
commands = nosetests -v tests/unit_tests.py --with-xcoverage --cover-package=udocker
[testenv:bandit]
commands = bandit udocker -f html -o bandit.html"""
    }

    stages {
        stage('Code fetching') {
            steps {
                checkout scm
            }
        }

        stage('Environment setup') {
            steps {
                PipRequirements(['pylint', 'nose', 'nosexcover', 'mock', 'bandit'], 'test-requirements.txt')
                ToxConfig(tox_envs, 'tox_jenkins.ini')
            }
            post {
                always {
                    archiveArtifacts artifacts: '*requirements.txt,*tox*.ini'
                }
            }
        }

        stage('Style analysis') {
            steps {
                ToxEnvRun('pylint', 'tox_jenkins.ini')
            }
            post {
                always {
                    WarningsReport('PyLint')
                }
            }
        }

        stage('Unit testing coverage') {
            steps {
                ToxEnvRun('cobertura', 'tox_jenkins.ini')
            }
            post {
                success {
                    CoberturaReport('**/coverage.xml')
                }
            }
        }

        stage('Security scanner') {
            steps {
                script {
                    try {
                        ToxEnvRun('bandit', 'tox_jenkins.ini')
                    }
                    catch(e) {
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
            post {
                always {
                    HTMLReport("", 'bandit.html', 'Bandit report')
                }
            }
        }

        stage('Metrics gathering') {
            agent {
                label 'sloc'
            }
            steps {
                checkout scm
                SLOCRun()
            }
            post {
                success {
                    SLOCPublish()
                }
            }
        }
    }
}
