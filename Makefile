NAME 		?= knocker
VIRTUAL_ENV 	?= env
DOCKERHUB_USERNAME?= horneds
VERSION 	?= $(shell cat $(CURDIR)/.version)


all: $(VIRTUAL_ENV)

$(VIRTUAL_ENV): $(CURDIR)/requirements.txt
	@[ -d $(VIRTUAL_ENV) ] || python -m venv $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install -r requirements.txt
	@touch $(VIRTUAL_ENV)


VERSION	?= minor

.PHONY: version
version: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install bump2version
	$(VIRTUAL_ENV)/bin/bump2version $(VERSION)
	git checkout master
	git pull
	git merge develop
	git checkout develop
	git push origin develop master
	git push --tags

.PHONY: minor
minor:
	make version VERSION=minor

.PHONY: patch
patch:
	make version VERSION=patch

.PHONY: major
major:
	make version VERSION=major


dev: $(VIRTUAL_ENV)
	$(VIRTUAL_ENV)/bin/uvicorn --reload $(NAME):app

test t: $(VIRTUAL_ENV)
	$(VIRTUAL_ENV)/bin/pytest tests.py

# Docker
# ------

docker:
	docker rmi --force `docker images -q '$(DOCKERHUB_USERNAME)/$(NAME)' | uniq` || true
	docker build -f $(CURDIR)/devops/Dockerfile -t $(DOCKERHUB_USERNAME)/$(NAME):$(VERSION) $(CURDIR)
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


