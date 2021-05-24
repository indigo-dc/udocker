@Library(['github.com/indigo-dc/jenkins-pipeline-library@release/2.1.0']) _

def projectConfig

pipeline {
    agent any

    stages {
        stage('SQA baseline dynamic stages') {
            when {
              anyOf {
                branch 'master'
                branch 'devel*'
                buildingTag()
                changeRequest target: 'master'
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
