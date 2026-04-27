pipeline {
    agent any

    environment {
        // Variables for Docker and Kubernetes
        DOCKER_IMAGE = 'starbucks-fastapi'
        // Specify your Docker registry here, e.g., 'your-dockerhub-username' or AWS ECR URL
        DOCKER_REGISTRY = '617029295065.dkr.ecr.ap-south-2.amazonaws.com'
        IMAGE_TAG = "${env.BUILD_ID}"
        
        // Define your credentials IDs set up in Jenkins
        KUBECONFIG_ID = 'k8s-kubeconfig'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup & Lint/Test') {
            steps {
                script {
                    echo "Setting up Python environment and running tests/linters"
                    // Optionally, run pytest or black here if you add tests later
                    sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building the Docker Image"
                    sh "docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${IMAGE_TAG} -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest ."
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    echo "Pushing Docker Image to AWS ECR"
                    // AWS CLI login
                    sh "aws ecr get-login-password --region ap-south-2 | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}"
                    sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${IMAGE_TAG}"
                    sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest"
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    echo "Deploying application to Kubernetes Cluster"
                    withKubeConfig(credentialsId: "${KUBECONFIG_ID}") {
                        // Update the deployment image to the newly built tag
                        sh "sed -i 's|image: starbucks-fastapi:latest|image: ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${IMAGE_TAG}|g' k8s/deployment.yaml"
                        
                        // Apply the Kubernetes manifests
                        sh "kubectl apply -f k8s/"
                        
                        // Verify deployment rollout
                        sh "kubectl rollout status deployment/starbucks-fastapi-deployment"
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Successfully deployed the Starbucks FastAPI app!"
        }
        failure {
            echo "Deployment failed. Check the logs."
        }
    }
}
