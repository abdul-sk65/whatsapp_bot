.PHONY: up down restart logs test test-server test-router clean help

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "WhatsApp Router System - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Build and start all services
	@echo "Building and starting services..."
	docker compose build
	docker compose up -d
	@echo "Services started successfully!"
	@echo "Router: http://localhost:8000"
	@echo "Server: http://localhost:8001"
	@echo ""
	@echo "Check health status:"
	@echo "  curl http://localhost:8000/health"
	@echo "  curl http://localhost:8001/health"

down: ## Stop and remove all services
	@echo "Stopping services..."
	docker compose down
	@echo "Services stopped successfully!"

restart: down up ## Restart all services

logs: ## Show logs from all services
	docker compose logs -f

logs-router: ## Show logs from router service only
	docker compose logs -f router

logs-server: ## Show logs from server service only
	docker compose logs -f server

test: test-server test-router ## Run all tests

test-server: ## Run tests for server service
	@echo "Running server tests..."
	cd server && uv run pytest -v

test-router: ## Run tests for router service
	@echo "Running router tests..."
	cd router && uv run pytest -v

test-server-docker: ## Run server tests in Docker
	@echo "Running server tests in Docker..."
	docker compose run --rm server uv run pytest -v

test-router-docker: ## Run router tests in Docker
	@echo "Running router tests in Docker..."
	docker compose run --rm router uv run pytest -v

clean: ## Clean up containers, images, and volumes
	@echo "Cleaning up..."
	docker compose down -v
	docker system prune -f
	@echo "Cleanup complete!"

status: ## Show status of all services
	docker compose ps

build: ## Build Docker images without starting services
	docker compose build

ngrok: ## Instructions for setting up ngrok
	@echo "To expose your router service with ngrok:"
	@echo ""
	@echo "1. Install ngrok: https://ngrok.com/download"
	@echo "2. Run: ngrok http 8000"
	@echo "3. Copy the HTTPS URL (e.g., https://abcd1234.ngrok.io)"
	@echo "4. In Meta Developer Console, set webhook URL to: https://abcd1234.ngrok.io/webhook"
	@echo "5. Set verify token to match your WHATSAPP_WEBHOOK_VERIFY_TOKEN"
	@echo ""

check-env: ## Check if required environment variables are set
	@echo "Checking environment variables..."
	@if [ -f .env ]; then \
		echo "✓ .env file exists"; \
	else \
		echo "✗ .env file not found! Copy .env.example to .env"; \
		exit 1; \
	fi
	@grep -q "WHATSAPP_PHONE_NUMBER_ID" .env && echo "✓ WHATSAPP_PHONE_NUMBER_ID set" || echo "✗ WHATSAPP_PHONE_NUMBER_ID not set"
	@grep -q "WHATSAPP_ACCESS_TOKEN" .env && echo "✓ WHATSAPP_ACCESS_TOKEN set" || echo "✗ WHATSAPP_ACCESS_TOKEN not set"
	@grep -q "WHATSAPP_WEBHOOK_VERIFY_TOKEN" .env && echo "✓ WHATSAPP_WEBHOOK_VERIFY_TOKEN set" || echo "✗ WHATSAPP_WEBHOOK_VERIFY_TOKEN not set"