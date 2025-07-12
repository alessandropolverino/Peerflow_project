# PeerFlow - Automated Peer Review System

A microservices-based peer review platform designed for MOOC environments, enabling teachers to create assignments and students to submit work and evaluate their peers' submissions through structured reviews.

This project was developed by a 3-person team (Ciaravola Giosuè, Della Corte Mario, Alessandro Polverino) in 10 days as the final exam project for the courses "Software Architectures for Enterprise System" and "DevOps Practices" of the Computer Engineering master degree. The implementation particularly focuses on demonstrating enterprise architecture principles and DevOps methodologies. Detailed reports on these topics can be found in the `doc` directory.

## What the System Does

PeerFlow is an automated peer review system that facilitates collaborative student evaluation processes in academic environments. The system supports:

- **Authentication & Profiling**: Role-based access control for teachers and students
- **Assignment Management**: Teachers can create assignments with descriptions, assessment rubrics, deadlines, and specify involved students
- **Student Submissions**: Students submit their work including text content and file attachments
- **Peer Review Process**: Automatic or manual assignment of peer reviewers, with structured evaluation based on predefined rubrics
- **Results Aggregation**: Collection and visualization of evaluation results for both students and teachers

## Installation

### Prerequisites

- Docker and Docker Compose
- Kubernetes (MicroK8s recommended)
- Jenkins for CI/CD
- Node.js and npm (for UI components and testing)
- Python 3.x (for backend services)
- Git with SSH access

### Git Setup

```bash
# Setup the local hooks
make setup-hooks

# Verify the hooks setup
make hooks-verify
```

## Usage

You can run the PeerFlow system using either Docker Compose (via makefile) or Kubernetes.

### Option 1: Using Makefile (Docker Compose)

#### Development Environment
```bash
# Start all services in development mode
make dev_start

# Stop all services
make dev_down

# Run tests for all services
make test_up

# Clean test environment
make test_clean
```

### Option 2: Using Kubernetes

#### Production Environment
```bash
# Start all services in production mode
kubectl apply -k kubernetes/overlays/prod

# Then start the UI
docker run -p 8888:3000 -d giosuciaravola/peerflow-ui-service:prod
```

#### Production Endpoints

You can use these endpoints to interact with the PeerFlow API in production (check the dockercompose for the development ports):

- **Authentication & Profiling**: API documentation at http://localhost:30010/docs
- **Assignment Management**: API documentation at http://localhost:30020/docs
- **Student Assignment Submissions**: API documentation at http://localhost:30030/docs
- **File System Submission Attachments**: Filesystem for document attachment at http://localhost:30031
- **Peer Review Assignment**: API documentation at http://localhost:30040/docs
- **Peer Review Processing**: API documentation at http://localhost:30050/docs
- **Orchestrator**: API documentation at http://localhost:30060/docs
- **PeerFlowUI**: Web application at  http://localhost:8888

## 📁 Project Structure

```
peerflow/
├── .gitignore                # Git ignore rules
├── Jenkinsfile               # Jenkins CI/CD pipeline configuration
├── README.md                 # Project documentation
├── makefile                  # Build automation and development commands
├── doc/                      # 📚 Documentation
├── kubernetes/               # ☸️ Kubernetes deployment configurations
├── local_hook/               # 🪝 Git hooks for local development
├── postman/                  # 🧪 API testing collections
├── remote_hook/              # 🪝 Git hooks for remote repository
└── src/                      # 💻 Source code (microservices architecture)
```

<details>
<summary><strong>📚 doc/</strong> - Documentation</summary>

```
doc/
├── LaTeX/                    # LaTeX documentation source files
└── UML/                      # UML diagrams and use case definitions
```
</details>

<details>
<summary><strong>☸️ kubernetes/</strong> - Deployment Configuration</summary>

```
kubernetes/
├── base/                     # Base kubernetes manifests
└── overlays/                 # Environment-specific Kubernetes overlays (test/prod)
```
</details>

<details>
<summary><strong>🪝 local_hook/</strong> - Local Git Hooks</summary>

```
local_hook/
├── pre-commit                # Runs unit tests before commits
└── pre-push                  # Prevents direct pushes to production branch
```
</details>

<details>
<summary><strong>🧪 postman/</strong> - API Testing</summary>

```
postman/
├── peerflow-integration-tests.json   # Integration test suite
└── peerflow-load-tests.json  # Load testing scenarios
```
</details>

<details>
<summary><strong>🪝 remote_hook/</strong> - Remote Git Hooks</summary>

```
remote_hook/
└── post-receive              # Triggers Jenkins pipeline on push
```
</details>

<details>
<summary><strong>💻 src/</strong> - Microservices Source Code</summary>

```
src/
├── AuthAndProfilingService/        # 🔐 Authentication and profiling service
├── AssignmentService/              # 📝 Assignment management service
├── AssignmentSubmissionService/    # 📤 Assignment submission service
├── ReviewAssignmentService/        # 👥 Peer review assignment service
├── ReviewProcessingService/        # ✏️ Peer review results service
├── Orchestrator/                   # 🎯 API gateway and orchestration
└── PeerFlowUI/                     # 🖥️ Frontend application (PeerFlowUI)
```
</details>

<details>
<summary><strong>📝 Example Service Directory</strong> - Service Structure</summary>

```
src/
├── src                     # 📂 Source code directory
├── test                    # 🧪 Test directory
├── .env.example            # 🔑 Environment variables
├── .gitignore              # 🚫 Git ignore rules
├── docker-compose.yml      # 🐳 Docker Compose configuration
├── Dockerfile              # 🐳 Dockerfile
├── Makefile                # 🛠️ Makefile for build and testing
├── pyproject.toml          # 🐍 Python project configuration
├── README.md               # 📖 Service documentation
└── requirements.txt        # 📦 Python dependencies
```