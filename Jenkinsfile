pipeline {
    agent any
    environment {
        // --- Docker Hub credentials ID configured in Jenkins ---
        REGISTRY_CREDENTIAL = 'dockerhublogin'
        DOCKER_REGISTRY = 'https://registry.hub.docker.com'

        // --- Docker image names - customize with your Docker Hub username ---
        DOCKER_USERNAME = 'giosuciaravola'
        /* 
            Service image name definition example:
            AUTH_SERVICE_IMAGE = "${DOCKER_USERNAME}/authentication-service"
        */
        AUTH_SERVICE_IMAGE = "${DOCKER_USERNAME}/peerflow-auth-profiling-service"
        ASSIGNMENT_SERVICE_IMAGE = "${DOCKER_USERNAME}/peerflow-assignment-service"
        ASSIGNMENT_SUBMISSION_SERVICE_IMAGE = "${DOCKER_USERNAME}/peerflow-assignment-submission-service"
        REVIEW_ASSIGNMENT_SERVICE_IMAGE = "${DOCKER_USERNAME}/peerflow-review-assignment-service"
        REVIEW_PROCESSING_SERVICE_IMAGE = "${DOCKER_USERNAME}/peerflow-processing-service"
        ORCHESTRATOR_SERVICE_IMAGE = "${DOCKER_USERNAME}/peerflow-orchestrator-service"

        // --- Docker image objects (will be populated during build) ---
        /*
            Service image object definition example:
            authenticationServiceImage = ""
        */
        authenticationServiceImage = ""
        assignmentServiceImage = ""
        assignmentSubmissionServiceImage = ""
        reviewAssignmentServiceImage = ""
        reviewProcessingServiceImage = ""
        orchestratorServiceImage = ""

        // --- Set environment-specific variables ---
        ENVIRONMENT = "${env.BRANCH_NAME == 'production' ? 'prod' : 'test'}"
        IMAGE_TAG = "${env.BRANCH_NAME == 'production' ? 'prod' : 'test'}"
        K8S_NAMESPACE = "peerflow-app-${ENVIRONMENT}"
    }

    stages {
        stage('Validate Branch') {
            steps {
                script {
                    echo "Validating branch: ${env.BRANCH_NAME}"
                    
                    // Check if branch is one of the allowed branches
                    if (env.BRANCH_NAME == 'production' || 
                        env.BRANCH_NAME == 'dev' || 
                        env.BRANCH_NAME ==~ /^release\/[0-9]+\.[0-9]+\.[0-9]+$/) {
                        
                        echo "✅ Branch '${env.BRANCH_NAME}' is valid. Pipeline will continue."
                    } else {
                        echo "❌ Branch '${env.BRANCH_NAME}' is not allowed to run this pipeline."
                        echo "   Only 'production', 'dev', and 'release/X.X.X' branches are permitted."
                        error "Pipeline aborted: Invalid branch name"
                    }
                }
            }
        }

        stage('Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                echo 'Building Docker images...'
                script {
                    // --- Build all images sequentially with appropriate tags ---
                    /*
                        Service image build example:
                        echo "Building Authentication Service with tag: ${IMAGE_TAG}..."
                        authenticationServiceImage = docker.build("${AUTH_SERVICE_IMAGE}:${IMAGE_TAG}", "./path/to/folder/with/dockerfile)
                    */
                    echo "Building Authentication Service with tag: ${IMAGE_TAG}..."
                    authenticationServiceImage = docker.build("${AUTH_SERVICE_IMAGE}:${IMAGE_TAG}", "./src/AuthAndProfilingService")

                    echo "Building Assignment Service with tag: ${IMAGE_TAG}..."
                    assignmentServiceImage = docker.build("${ASSIGNMENT_SERVICE_IMAGE}:${IMAGE_TAG}", "./src/AssignmentService")

                    echo "Building Assignment Submission Service with tag: ${IMAGE_TAG}..."
                    assignmentSubmissionServiceImage = docker.build("${ASSIGNMENT_SUBMISSION_SERVICE_IMAGE}:${IMAGE_TAG}", "./src/AssignmentSubmissionService")                
                
                    echo "Building Review Assignment Service with tag: ${IMAGE_TAG}..."
                    reviewAssignmentServiceImage = docker.build("${REVIEW_ASSIGNMENT_SERVICE_IMAGE}:${IMAGE_TAG}", "./src/ReviewAssignmentService")

                    echo "Building Review Processing Service with tag: ${IMAGE_TAG}..."
                    reviewProcessingServiceImage = docker.build("${REVIEW_PROCESSING_SERVICE_IMAGE}:${IMAGE_TAG}", "./src/ReviewProcessingService")

                    echo "Building Orchestrator Service with tag: ${IMAGE_TAG}..."
                    orchestratorServiceImage = docker.build("${ORCHESTRATOR_SERVICE_IMAGE}:${IMAGE_TAG}", "./src/Orchestrator")
                } 
            }
        }

        stage('Push Docker Images') {
            environment {
                registryCredential = "${REGISTRY_CREDENTIAL}"
            }
            steps {
                echo 'Pushing Docker images to Docker Hub...'
                script {
                    docker.withRegistry("${DOCKER_REGISTRY}", registryCredential) {
                        // --- Push all images sequentially to Docker Hub with appropriate tags ---
                        /*
                            Service image push example:
                            echo "Pushing Authentication Service with thag: ${IMAGE_TAG}..."
                            authenticationServiceImage.push("${IMAGE_TAG}")
                        */
                        echo "Pushing Authentication Service with thag: ${IMAGE_TAG}..."
                        authenticationServiceImage.push("${IMAGE_TAG}")

                        echo "Pushing Assignment Service with thag: ${IMAGE_TAG}..."
                        assignmentServiceImage.push("${IMAGE_TAG}")

                        echo "Pushing Assignment Submission Service with thag: ${IMAGE_TAG}..."
                        assignmentSubmissionServiceImage.push("${IMAGE_TAG}")

                        echo "Pushing Review Assignment Service with thag: ${IMAGE_TAG}..."
                        reviewAssignmentServiceImage.push("${IMAGE_TAG}")

                        echo "Pushing Review Processing Service with thag: ${IMAGE_TAG}..."
                        reviewProcessingServiceImage.push("${IMAGE_TAG}")

                        echo "Pushing Orchestrator Service with thag: ${IMAGE_TAG}..."
                        orchestratorServiceImage.push("${IMAGE_TAG}")
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo "Deploying to Kubernetes (${ENVIRONMENT} environment)"
                script {
                    // Check if kustomization.yaml exists before deploying
                    def kustomizationExists = fileExists("kubernetes/overlays/${ENVIRONMENT}/kustomization.yaml")
                    
                    if (kustomizationExists) {
                        // --- Deploy all services to Kubernetes ---
                        sh """
                            echo "Deploying to ${K8S_NAMESPACE} namespace..."
                            microk8s kubectl apply -k kubernetes/overlays/${ENVIRONMENT}/

                            echo "Waiting for deployments..."
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/auth-profiling-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/assignment-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/assignment-submission-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/review-assignment-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/processing-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/orchestrator-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/mongodb-auth-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/mongodb-assignment-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/mongodb-assignment-submission-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/mongodb-review-assignment-service -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/seaweedfs-master -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/seaweedfs-filer -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/seaweedfs-volume -n ${K8S_NAMESPACE}
                            microk8s kubectl wait --for=condition=available --timeout=300s deployment/mongodb-processing-service -n ${K8S_NAMESPACE}

                            sleep 10
                            
                            echo "✅ Cluster is ready!"
                            microk8s kubectl get all -n ${K8S_NAMESPACE}
                        """
                    } else {
                        echo "⚠️ Skipping deployment: kustomization.yaml not found in kubernetes/overlays/${ENVIRONMENT}/"
                    }
                }
            }
        }

        stage('Setup Test Environment') {
            when {
                // Only run this stage when not on production branch
                not { branch 'production' }
            }
            steps {
                echo 'Setting up test environment...'
                script {
                    // --- Set up test environment specific configurations ---
                    sh """
                        mkdir -p reports
                        echo "✅ Test environment ready!"
                    """
                }
            }
        }

        stage('Integration Tests') {
            when {
                // Only run this stage when not on production branch
                not { branch 'production' }
            }
            steps {
                echo 'Running integration tests...'
                script {
                    // Check if postman test file exists before running tests
                    def postmanTestExists = fileExists('postman/peerflow-api-tests.json')
                    
                    if (postmanTestExists) {
                        // --- Run integration tests ---
                        sh '''
                            newman run postman/peerflow-api-tests.json \
                                --reporters cli,htmlextra,json \
                                --reporter-htmlextra-export reports/integration-test-report.html \
                                --reporter-json-export reports/integration-test-results.json \
                                --timeout-request 30000 \
                                --delay-request 1000
                        '''
                    } else {
                        echo '⚠️ Skipping integration tests: postman/peerflow-api-tests.json not found'
                    }
                }
            }
            post {
                always {
                    // Archive integration test results
                    script {
                        if (fileExists('reports/integration-test-report.html')) {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'reports',
                                reportFiles: 'integration-test-report.html',
                                reportName: 'Integration Test Report'
                            ])
                        }
                        if (fileExists('reports/integration-test-results.json')) {
                            archiveArtifacts artifacts: 'reports/integration-test-results.json', fingerprint: true
                        }
                    }
                }
                failure {
                    echo '❌ Integration tests failed!'
                }
            }
        }

        stage('Load Testing') {
            when {
                // Run on all branches except production and dev
                allOf {
                    not { branch 'production' }
                    not { branch 'dev' }
                }
            }
            steps {
                // Run load tests
                echo 'Running load tests...'
                script {
                    // Check if postman load test file exists before running tests
                    def postmanLoadTestExists = fileExists('postman/peerflow-load-tests.json')
                    
                    if (postmanLoadTestExists) {
                        sh '''
                            echo "Starting load testing with Newman..."
                            newman run postman/peerflow-load-tests.json \
                                --reporters cli,htmlextra,json \
                                --reporter-htmlextra-export reports/load-test-report.html \
                                --reporter-json-export reports/load-test-results.json \
                                --iteration-count 20 \
                                --timeout-request 2000 \
                                --delay-request 5
                            
                            echo "Load testing completed!"
                        '''
                    } else {
                        echo '⚠️ Skipping load tests: postman/peerflow-load-tests.json not found'
                    }
                }
            }
            post {
                always {
                    script {
                        // Archive load test results
                        if (fileExists('reports/load-test-report.html')) {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'reports',
                                reportFiles: 'load-test-report.html',
                                reportName: 'Load Test Report'
                            ])
                        }
                        if (fileExists('reports/load-test-results.json')) {
                            archiveArtifacts artifacts: 'reports/load-test-results.json', fingerprint: true
                        }
                    }
                }
                failure {
                    echo 'Load tests failed or performance degradation detected!'
                    script {
                        sh '''
                            echo "⚠️ Performance issues detected in load tests"
                            
                            echo "\nChecking current pod metrics..."
                            microk8s kubectl top pods -n ${K8S_NAMESPACE}
                        '''
                    }
                }
            }
        }

        stage('Force Merge to Production') {
            when {
                // Run on all branches except production and dev
                allOf {
                    not { branch 'production' }
                    not { branch 'dev' }
                }
            }
            steps {
                echo 'Integration and load tests passed! Force merging to production branch...'
                script {
                    // --- Force merge current branch to production ---
                    sshagent(['ssh_agent_key']) {
                        sh '''
                            # Configure git user
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@localhost"
                            
                            # Get current branch name using Jenkins environment variable
                            CURRENT_BRANCH="${BRANCH_NAME}"
                            echo "Current branch from Jenkins: $CURRENT_BRANCH"
                            
                            # Fetch latest changes
                            git fetch origin
                            
                            # Switch to production branch
                            git checkout production
                            
                            # Force merge production to match the staging commit
                            git merge --ff-only origin/$CURRENT_BRANCH
                            
                            # Force push to remote (this overwrites production completely)
                            git push origin production
                            
                            echo "✅ Successfully force-merged $CURRENT_BRANCH ($CURRENT_COMMIT) into productiond"
                        '''
                    }
                }
            }
        }
    }
    post {
        always {
            echo 'Pipeline completed!'
            // Clean up only if not on production branch
            script {
                if (env.BRANCH_NAME != 'production') {
                    // --- Tear down the test cluster ---
                    try {
                        sh "microk8s kubectl delete namespace ${K8S_NAMESPACE} || true"
                        echo '✅ Test cluster torn down successfully!'
                    } catch (Exception e) {
                        echo "Could not delete namespace: ${e.getMessage()}"
                    }
                } else {
                    echo '✅ Keeping production cluster up!'
                }
            }
            
            // --- Clean workspace but keep reports ---
            echo 'Cleaning workspace...'
            cleanWs(patterns: [[pattern: 'reports/**', type: 'EXCLUDE']], deleteDirs: true)
        }
        success {
            script {
                if (env.BRANCH_NAME == 'production') {
                    echo '✅ Pipeline completed successfully! PeerFlow is accessible.'
                } else {
                    echo '✅ Pipeline completed successfully!'
                }
            }
        }
        failure {
            echo '❌ Pipeline failed!'
        }
    }
}