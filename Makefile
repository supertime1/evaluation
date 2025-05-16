# Database configuration
export DATABASE_URL=postgresql://evaluation_user:evaluation@localhost:5432/evaluation_db

# Clear specific tables
clear-results:
	@echo "Clearing test_results table..."
	psql $(DATABASE_URL) -c "TRUNCATE test_results CASCADE;"

clear-test-cases:
	@echo "Clearing test_cases table..."
	psql $(DATABASE_URL) -c "TRUNCATE test_cases CASCADE;"

clear-runs:
	@echo "Clearing runs table..."
	psql $(DATABASE_URL) -c "TRUNCATE runs CASCADE;"

clear-experiments:
	@echo "Clearing experiments table..."
	psql $(DATABASE_URL) -c "TRUNCATE experiments CASCADE;"

clear-users:
	@echo "Clearing users table..."
	psql $(DATABASE_URL) -c "TRUNCATE users CASCADE;"

# Clear all data tables
clear-all: clear-results clear-test-cases clear-runs clear-experiments
	@echo "All evaluation data cleared."

# Reset full database (including users)
reset-db: clear-all clear-users
	@echo "Database reset complete."

# Generate new superuser
create-superuser:
	@echo "Creating superuser..."
	python -m scripts.set_superuser admin@example.com

# Run migrations
migrate:
	@echo "Running database migrations..."
	alembic upgrade head

# Help command
help:
	@echo "Available commands:"
	@echo "  make clear-results     - Clear test results table"
	@echo "  make clear-test-cases  - Clear test cases table"
	@echo "  make clear-runs        - Clear runs table"
	@echo "  make clear-experiments - Clear experiments table"
	@echo "  make clear-users       - Clear users table"
	@echo "  make clear-all         - Clear all evaluation data tables"
	@echo "  make reset-db          - Reset entire database"
	@echo "  make create-superuser  - Create admin superuser"
	@echo "  make migrate           - Run database migrations"

.PHONY: clear-results clear-test-cases clear-runs clear-experiments clear-users clear-all reset-db create-superuser migrate help