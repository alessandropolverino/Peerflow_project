# Makefile for PeerFlow
# Compatible with Windows 11, Linux, and macOS

# Variables
HOOKS_DIR = .git/hooks
LOCAL_HOOKS_DIR = local_hook
TEMPLATE_FILE = .gitmessage

# Single command to setup git-hooks
.PHONY: setup-hooks
setup-hooks:
	@echo "🚀 Setting up PeerFlow git hooks and commit template..."
	@echo ""
	@echo "📁 Copying git hooks from $(LOCAL_HOOKS_DIR) to $(HOOKS_DIR)..."
	@if [ ! -d "$(HOOKS_DIR)" ]; then \
		echo "❌ Error: .git/hooks directory not found. Are you in a git repository?"; \
		exit 1; \
	fi
	@if [ ! -d "$(LOCAL_HOOKS_DIR)" ]; then \
		echo "❌ Error: $(LOCAL_HOOKS_DIR) directory not found."; \
		exit 1; \
	fi
	@cp $(LOCAL_HOOKS_DIR)/pre-commit $(HOOKS_DIR)/pre-commit || (echo "❌ Failed to copy pre-commit hook" && exit 1)
	@cp $(LOCAL_HOOKS_DIR)/pre-push $(HOOKS_DIR)/pre-push || (echo "❌ Failed to copy pre-push hook" && exit 1)
	@cp $(LOCAL_HOOKS_DIR)/prepare-commit-msg $(HOOKS_DIR)/prepare-commit-msg || (echo "❌ Failed to copy prepare-commit-msg hook" && exit 1)
	@echo "✅ Hooks copied successfully"
	@echo ""
	@echo "🔧 Setting executable permissions on hooks..."
	@chmod +x $(HOOKS_DIR)/pre-commit || echo "⚠️  Warning: Could not set permissions on pre-commit (may work anyway on Windows)"
	@chmod +x $(HOOKS_DIR)/pre-push || echo "⚠️  Warning: Could not set permissions on pre-push (may work anyway on Windows)"
	@chmod +x $(HOOKS_DIR)/prepare-commit-msg || echo "⚠️  Warning: Could not set permissions on prepare-commit-msg (may work anyway on Windows)"
	@echo "✅ Permissions set"
	@echo ""
	@echo "📝 Setting up commit message template..."
	@if [ ! -f "$(TEMPLATE_FILE)" ]; then \
		echo "❌ Error: $(TEMPLATE_FILE) not found in root directory."; \
		exit 1; \
	fi
	@git config commit.template $(TEMPLATE_FILE)
	@echo "✅ Commit template configured"
	@echo ""
	@echo "✅ All git hooks and commit template setup complete!"
	@echo ""
	@echo "Installed hooks:"
	@echo "  - pre-commit (runs unit tests)"
	@echo "  - pre-push (prevents direct production pushes)"
	@echo "  - prepare-commit-msg (provides commit template)"
	@echo ""
	@echo "Usage: Run 'git commit' (without -m) to use the template"

# Verify installation
.PHONY: hooks-verify
hooks-verify:
	@echo "🔍 Verifying git hooks installation..."
	@echo ""
	@echo "Checking hook files:"
	@ls -la $(HOOKS_DIR)/pre-commit $(HOOKS_DIR)/pre-push $(HOOKS_DIR)/prepare-commit-msg 2>/dev/null || echo "❌ Some hooks are missing"
	@echo ""
	@echo "Current commit template setting:"
	@git config --get commit.template || echo "❌ No commit template configured"
	@echo ""
	@echo "Git repository status:"
	@git status --porcelain | head -5 || echo "📋 Repository is clean"

SHARED_NETWORK_NAME = peerflow-global-network

AUTH_SERVICE_DIR = src/AuthAndProfilingService
AUTH_SERVICE_CONTAINER = auth-service

ASSIGN_SERVICE_DIR = src/AssignmentService
ASSIGN_SERVICE_CONTAINER = assignment-service

ASSIGN_SUBM_SERVICE_DIR = src/AssignmentSubmissionService
ASSIGN_SUBM_CONTAINER = assignment-submission-service

REVIEW_ASSIGN_SERVICE_DIR = src/ReviewAssignmentService
REVIEW_ASSIGN_CONTAINER = review-assignment-service

REVIEW_PROC_SERVICE_DIR = src/ReviewProcessingService
REVIEW_PROC_CONTAINER = processing-service

ORCHESTRATOR_SERVICE_DIR = src/Orchestrator
ORCHESTRATOR_CONTAINER = orchestrator-service

PEERFLOW_UI_SERVICE_DIR = src/PeerFlowUI
PEERFLOW_UI_CONTAINER = peerflow-ui-service

dev_start: setup_network dev_start_auth dev_start_assignment_service dev_start_assignment_submission_service dev_start_review_assignment_service dev_start_review_processing_service dev_start_orchestrator dev_start_peerflow_ui
	@echo "------------ All services started successfully ------------"

dev_down:
	@echo "Stopping all services..."
	cd $(AUTH_SERVICE_DIR) && make dev_down
	cd $(ASSIGN_SERVICE_DIR) && make dev_down
	cd $(ASSIGN_SUBM_SERVICE_DIR) && make dev_down
	cd $(REVIEW_ASSIGN_SERVICE_DIR) && make dev_down
	cd $(REVIEW_PROC_SERVICE_DIR) && make dev_down
	cd $(ORCHESTRATOR_SERVICE_DIR) && make dev_down
	cd $(PEERFLOW_UI_SERVICE_DIR) && make dev_down
	@echo "All services stopped."
	@echo "Cleaning up shared network '$(SHARED_NETWORK_NAME)'..."
	docker network inspect $(SHARED_NETWORK_NAME) >/dev/null 2>&1 && \
		docker network rm $(SHARED_NETWORK_NAME) || \
		echo "Network '$(SHARED_NETWORK_NAME)' does not exist, skipping cleanup."

test_up:
	@echo "Running tests for all services..."
	cd $(AUTH_SERVICE_DIR) && make test_up
	cd $(ASSIGN_SERVICE_DIR) && make test_up
	cd $(ASSIGN_SUBM_SERVICE_DIR) && make test_up
	cd $(REVIEW_ASSIGN_SERVICE_DIR) && make test_up
	cd $(REVIEW_PROC_SERVICE_DIR) && make test_up
	cd $(ORCHESTRATOR_SERVICE_DIR) && make test_up
	@echo "All services tests are runned."

test_clean:
	@echo "Cleaning test environment for all services..."
	cd $(AUTH_SERVICE_DIR) && make test_clean
	cd $(ASSIGN_SERVICE_DIR) && make test_clean
	cd $(ASSIGN_SUBM_SERVICE_DIR) && make test_clean
	cd $(REVIEW_ASSIGN_SERVICE_DIR) && make test_clean
	cd $(REVIEW_PROC_SERVICE_DIR) && make test_clean
	cd $(ORCHESTRATOR_SERVICE_DIR) && make test_clean
	@echo "All services test environment cleaned."

setup_network:
	@echo "Setting up shared network '$(SHARED_NETWORK_NAME)'..."
	docker network inspect $(SHARED_NETWORK_NAME) >/dev/null 2>&1 || \
		docker network create $(SHARED_NETWORK_NAME)
	@echo "Network '$(SHARED_NETWORK_NAME)' is ready."

dev_start_auth:
	@echo "Starting AuthService..."
	cd $(AUTH_SERVICE_DIR) && make dev_up
	@CONTAINER_ID=$$(docker compose -f $(AUTH_SERVICE_DIR)/docker-compose.dev.yml ps -q $(AUTH_SERVICE_CONTAINER)); \
		if [ -n "$$CONTAINER_ID" ]; then \
				docker network connect $(SHARED_NETWORK_NAME) $$CONTAINER_ID; \
				echo "AuthService is connected to the shared network."; \
		else \
				echo "Error: AuthService container not found"; \
				exit 1; \
		fi

dev_start_assignment_service:
	@echo "Starting AssignmentService..."
	cd $(ASSIGN_SERVICE_DIR) && make dev_up
	@CONTAINER_ID=$$(docker compose -f $(ASSIGN_SERVICE_DIR)/docker-compose.dev.yml ps -q $(ASSIGN_SERVICE_CONTAINER)); \
		if [ -n "$$CONTAINER_ID" ]; then \
				docker network connect $(SHARED_NETWORK_NAME) $$CONTAINER_ID; \
				echo "AssignmentService is connected to the shared network."; \
		else \
				echo "Error: AssignmentService container not found"; \
				exit 1; \
		fi

dev_start_assignment_submission_service:
	@echo "Starting Assignment Submission Service..."
	cd $(ASSIGN_SUBM_SERVICE_DIR) && make dev_up
	@CONTAINER_ID=$$(docker compose -f $(ASSIGN_SUBM_SERVICE_DIR)/docker-compose.dev.yml ps -q $(ASSIGN_SUBM_CONTAINER)); \
		if [ -n "$$CONTAINER_ID" ]; then \
				docker network connect $(SHARED_NETWORK_NAME) $$CONTAINER_ID; \
				echo "Assignment Submission Service is connected to the shared network."; \
		else \
				echo "Error: Assignment Submission Service container not found"; \
				exit 1; \
		fi
	@SEAWEED_FS_ID=$$(docker compose -f $(ASSIGN_SUBM_SERVICE_DIR)/docker-compose.dev.yml ps -q fs-s3); \
		if [ -n "$$SEAWEED_FS_ID" ]; then \
			docker network connect $(SHARED_NETWORK_NAME) $$SEAWEED_FS_ID; \
			echo "S3 FILER is connected to the shared network."; \
		else \
			echo "Error: S3 FILER container not found"; \
			exit 1; \
		fi

dev_start_review_assignment_service:
	@echo "Starting Review Assignment Service..."
	cd $(REVIEW_ASSIGN_SERVICE_DIR) && make dev_up
	@CONTAINER_ID=$$(docker compose -f $(REVIEW_ASSIGN_SERVICE_DIR)/docker-compose.dev.yml ps -q $(REVIEW_ASSIGN_CONTAINER)); \
		if [ -n "$$CONTAINER_ID" ]; then \
				docker network connect $(SHARED_NETWORK_NAME) $$CONTAINER_ID; \
				echo "Review Assignment Service is connected to the shared network."; \
		else \
				echo "Error: Review Assignment Service container not found"; \
				exit 1; \
		fi

dev_start_review_processing_service:
	@echo "Starting Review Processing Service..."
	cd $(REVIEW_PROC_SERVICE_DIR) && make dev_up
	@CONTAINER_ID=$$(docker compose -f $(REVIEW_PROC_SERVICE_DIR)/docker-compose.dev.yml ps -q $(REVIEW_PROC_CONTAINER)); \
		if [ -n "$$CONTAINER_ID" ]; then \
				docker network connect $(SHARED_NETWORK_NAME) $$CONTAINER_ID; \
				echo "Review Processing Service is connected to the shared network."; \
		else \
				echo "Error: Review Processing Service container not found"; \
				exit 1; \
		fi

dev_start_orchestrator:
	@echo "Starting Orchestrator..."
	cd $(ORCHESTRATOR_SERVICE_DIR) && make dev_up
	@CONTAINER_ID=$$(docker compose -f $(ORCHESTRATOR_SERVICE_DIR)/docker-compose.dev.yml ps -q $(ORCHESTRATOR_CONTAINER)); \
		if [ -n "$$CONTAINER_ID" ]; then \
				docker network connect $(SHARED_NETWORK_NAME) $$CONTAINER_ID; \
				echo "Orchestrator is connected to the shared network."; \
		else \
				echo "Error: Orchestrator container not found"; \
				exit 1; \
		fi

dev_start_peerflow_ui:
	@echo "Starting PeerFlow UI Service..."
	cd $(PEERFLOW_UI_SERVICE_DIR) && make dev_up
	@CONTAINER_ID=$$(docker compose -f $(PEERFLOW_UI_SERVICE_DIR)/docker-compose.dev.yml ps -q $(PEERFLOW_UI_CONTAINER)); \
		if [ -n "$$CONTAINER_ID" ]; then \
				docker network connect $(SHARED_NETWORK_NAME) $$CONTAINER_ID; \
				echo "PeerFlow UI Service is connected to the shared network."; \
		else \
				echo "Error: PeerFlow UI Service container not found"; \
				exit 1; \
		fi

# Help target
.PHONY: help
help:
	@echo "PeerFlow Git Hooks Setup Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  setup-hooks    - Install all git hooks and setup commit template (default)"
	@echo "  hooks-verify   - Verify git hooks installation"
	@echo "  dev_start      - Start all services in development mode"
	@echo "  dev_down       - Stop all services in development mode"
	@echo "  test_up        - Run tests for all services"
	@echo "  test_clean     - Clean test environment for all services"
	@echo "  dev_start_auth - Start AuthService in development mode"
	@echo "  dev_start_assignment_service - Start AssignmentService in development mode"
	@echo "  dev_start_assignment_submission_service - Start Assignment Submission Service in development mode"
	@echo "  dev_start_review_assignment_service - Start Review Assignment Service in development mode
	@echo "  dev_start_review_processing_service - Start Review Processing Service in development mode"
	@echo "  dev_start_orchestrator - Start Orchestrator in development mode"
	@echo "  dev_start_peerflow_ui - Start PeerFlow UI Service in development mode"
	@echo "  help           - Show this help message"
	@echo ""
	@echo "Usage example:"
	@echo "  make setup-hooks    # Install everything"