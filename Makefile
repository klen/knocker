NAME 		?= knocker
VIRTUAL_ENV 	?= .venv
DOCKERHUB_USERNAME?= horneds


all: $(VIRTUAL_ENV)

$(VIRTUAL_ENV): uv.lock
	@echo "Setting up virtual environment and installing dependencies..."
	@uv sync
	@uv run pre-commit install
	@touch $(VIRTUAL_ENV) # Create a marker file

export-requirements:
	@echo "Exporting requirements..."
	@uv export \
		--no-dev \
		--no-hashes \
		--no-annotate \
		--no-emit-project \
		> $(CURDIR)/requirements.txt
	@echo "Requirements exported successfully."

.PHONY: version v
version v:
	@echo "Current project version:"
	@uv version --short

RELEASE	?= minor

.PHONY: release
release: $(VIRTUAL_ENV)
	@echo "Preparing release: $(RELEASE) version bump..."
	@git checkout develop
	@git pull
	@git checkout master
	@git pull
	@git merge develop
	@uvx bump-my-version bump $(RELEASE)
	@uv lock
	@git commit -am "build(release): `uv version --short`"
	@git tag `uv version --short`
	@git checkout develop
	@git merge master
	@git push --tags origin develop master
	@echo "Release process complete for `uv version --short`."

.PHONY: minor
minor:
	make release RELEASE=minor

.PHONY: patch
patch:
	make release RELEASE=patch

.PHONY: major
major:
	make release RELEASE=major

dev:
	uv run uvicorn --reload $(NAME).app:app

test t:
	uv run pytest tests

mypy:
	uv run mypy

ruff:
	uv run ruff check $(NAME)

# Docker
# ------

VERSION 	?= $(shell uv version --short)
docker: export-requirements
	docker rmi --force `docker images -q '$(DOCKERHUB_USERNAME)/$(NAME)' | uniq` || true
	docker build --platform=linux/amd64 -f $(CURDIR)/devops/Dockerfile -t $(DOCKERHUB_USERNAME)/$(NAME):$(VERSION) $(CURDIR)
	docker tag $(DOCKERHUB_USERNAME)/$(NAME):$(VERSION) $(DOCKERHUB_USERNAME)/$(NAME):latest

docker-shell: docker
	docker run -it --rm --name $(NAME) $(DOCKERHUB_USERNAME)/$(NAME):latest bash

docker-run run: docker
	docker run -it --rm -p 80:8000 --name $(NAME) $(DOCKERHUB_USERNAME)/$(NAME):latest

docker-upload: docker
	docker push $(DOCKERHUB_USERNAME)/$(NAME):$(VERSION)
	docker push $(DOCKERHUB_USERNAME)/$(NAME):latest
	docker run --rm \
	    -v $(CURDIR):/data \
	    -e DOCKERHUB_USERNAME=$(DOCKERHUB_USERNAME) \
	    -e DOCKERHUB_PASSWORD=$(shell cat $(CURDIR)/.ignore/dockerhub) \
	    -e DOCKERHUB_REPO_NAME=$(NAME) \
	    sheogorath/readme-to-dockerhub
