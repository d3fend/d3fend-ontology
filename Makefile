SHELL ?= /usr/local/bin/bash

clean:
	rm -Rf build/*

install-deps:
	mkdir -p bin
	curl https://d3fend.pages.mitre.org/deps/robot/robot > bin/robot
	chmod +x bin/robot
	curl https://d3fend.pages.mitre.org/deps/robot/robot.jar > bin/robot.jar

report:
	./bin/robot report -i d3fend.owl

# WTH robot!? ttl isn't just default, it's only thing? DELETE TARGET AFTER DISCUSSION
robot-fails-with-ttl-in-d3fend-robot_owl-file-dammit:
	./bin/robot query --format owl \
		--input d3fend-webprotege.owl \
		--query Restrictions-as-ObjectProperties.rq build/d3fend-robot.owl

robot-res-as-prop: ## Extracts and translates just restrictions -> object property assertions
	./bin/robot query --input d3fend-webprotege.owl \
		--query Restrictions-as-ObjectProperties.rq build/d3fend-res-as-prop.owl
#	./bin/robot convert --input d3fend-robot.owl --output d3fend-res-as-prop.owl

robot: robot-res-as-prop ## Adds in object property assertions for class property restrictions
	./bin/robot merge --input d3fend-webprotege.owl \
		--input build/d3fend-res-as-prop.owl \
		--output build/d3fend-robot.owl

builddir:
	mkdir -p build/

build: 	builddir robot filter-architecture-MIREOT ## npm run build and move to public folder
	cp build/d3fend-robot.owl d3fend-full.owl  # TODO refactor
	pipenv run python process.py
	SSL_CERT_FILE=~/MITRE.crt pipenv run python makecsv.py

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

clean:
	rm -f d3fend.*
	rm -f d3fend-webprotege.json 
	rm -f d3fend-architecture*
	rm -f d3fend-full.owl
	rm -f build/*

all: build ## the whole thing

help: ##print out this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help
