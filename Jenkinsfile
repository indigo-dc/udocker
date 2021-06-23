@Library(['github.com/indigo-dc/jenkins-pipeline-library@release/2.1.0']) _

def projectConfig

pipeline {
    agent { label 'udocker' }

    options {
        lock('udocker')
        throttle(['StandaloneByNode'])
    }

    stages {
        stage('SQA baseline dynamic stages') {
            when {
              anyOf {
                branch 'master'
                branch 'devel3'
                buildingTag()
                changeRequest target: 'master'
                changeRequest target: 'devel3'
              }
            }
            steps {
                script {
                    projectConfig = pipelineConfig()
                    buildStages(projectConfig)
                }
            }
            post {
                cleanup {
                    cleanWs()
                }
            }
        }
    }
}
