export_dep:
	@echo "Generating requirements.txt..."
	pip freeze > requirements.txt

DOCKER_TEST_CONTAINER_NAME=auth-test-runner


dev_up: 
	@echo "Starting development configuration..."
	docker compose -f docker-compose.dev.yml up --build -d

dev_down:
	@echo "Stopping development configuration..."
	docker compose -f docker-compose.dev.yml down

dev_logs:
	@echo "Showing logs for development configuration..."
	docker compose -f docker-compose.dev.yml logs -f

dev_reload: dev_down dev_up
	@echo "Development configuration reloaded."

dev_clean: dev_down
	@echo "Cleaning development environment..."
	docker compose -f docker-compose.dev.yml down -v

# Test commands
test_up:
	@echo "Running tests..."
	docker-compose -f docker-compose.test.yml run --build --rm -T ${DOCKER_TEST_CONTAINER_NAME}

test_down:
	@echo "Stopping test environment..."
	docker-compose -f docker-compose.test.yml down

test_logs:
	@echo "Showing test logs..."
	docker-compose -f docker-compose.test.yml logs ${DOCKER_TEST_CONTAINER_NAME}

test_clean: test_down
	@echo "Cleaning test environment..."
	docker-compose -f docker-compose.test.yml down -v