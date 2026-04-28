test:
	pytest

build:
	docker build -t deployment-report:latest .

scan:
	trivy image deployment-report:latest

