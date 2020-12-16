SHELL ?= /usr/local/bin/bash

install-deps:
	mkdir -p bin
	curl https://d3fend.pages.mitre.org/deps/robot/robot > bin/robot
	chmod +x bin/robot
	curl https://d3fend.pages.mitre.org/deps/robot/robot.jar > bin/robot.jar

report:
	./bin/robot report -i d3fend.owl

build: ## npm run build and move to public folder
	pipenv run python process.py
	pipenv run python makecsv.py

all: build ## the whole thing

help: ##print out this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help
