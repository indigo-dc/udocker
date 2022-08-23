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
                branch 'dev*'
                buildingTag()
                changeRequest target: 'master'
                changeRequest target: 'dev-v1.4'
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
