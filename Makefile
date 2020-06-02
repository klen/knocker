NAME 		?= knocker
VIRTUAL_ENV 	?= env
DOCKERHUB 	?= horneds
VERSION ?= $(shell cat $(CURDIR)/.version)


all: $(VIRTUAL_ENV)

$(VIRTUAL_ENV): $(CURDIR)/requirements.txt
	@[ -d $(VIRTUAL_ENV) ] || virtualenv --python=python3 $(VIRTUAL_ENV)
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
	$(VIRTUAL_ENV)/bin/uvicorn --port 5000 --reload $(NAME):app

test t: $(VIRTUAL_ENV)
	$(VIRTUAL_ENV)/bin/pytest tests.py

# Docker
# ------

docker:
	docker build -f $(CURDIR)/devops/Dockerfile -t $(DOCKERHUB)/$(NAME):$(VERSION) $(CURDIR)
	docker tag $(DOCKERHUB)/$(NAME):$(VERSION) $(DOCKERHUB)/$(NAME):latest

docker-run: docker
	docker run -it --rm -p 5000:8000 --name $(NAME) $(DOCKERHUB)/$(NAME):latest

docker-upload:
	docker push $(DOCKERHUB)/$(NAME):$(VERSION)
	docker push $(DOCKERHUB)/$(NAME):latest
