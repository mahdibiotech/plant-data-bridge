up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f

test-etl:
	cd etl && python -m pytest -q

test-backend:
	cd backend && mvn test
