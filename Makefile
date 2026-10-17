.PHONY: ingest test holdout run-backend run-frontend

ingest:
	py -m backend.copilot.ingest.loader

test:
	py -m pytest backend/tests -v

holdout:
	py scripts/make_holdout.py
	py -m pytest backend/tests/test_holdout.py -v

run-backend:
	uvicorn backend.copilot.api.main:app --reload --port 8000

run-frontend:
	npm run dev --prefix frontend
