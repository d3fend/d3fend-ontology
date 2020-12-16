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

filter-architecture-star:
	./bin/robot extract --method STAR \
    	--input d3fend.owl \
    	--term-file termfile-architecture.txt \
    	--output d3fend-architecture.owl

filter-architecture-MIREOT:
	./bin/robot extract --method MIREOT \
    	--input d3fend.owl \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#NetworkNode" \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#Application" \
    	--output d3fend-architecture.owl

all: build ## the whole thing

help: ##print out this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help
