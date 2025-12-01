.PHONY: dev ingest-sample compute-features test migrate clean

dev:
	docker-compose up --build

ingest-sample:
	docker compose exec backend python -m app.services.ingestion --source /app/sample_data/sector_time_series.csv

compute-features:
	docker compose exec backend python -m app.services.compute_all

test:
	docker compose exec backend pytest

migrate:
	docker compose exec backend alembic upgrade head

clean:
	docker-compose down -v

