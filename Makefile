SHELL ?= /usr/local/bin/bash

clean:
	rm -f d3fend.*
	rm -f d3fend-webprotege.json 
	rm -f d3fend-architecture*
	rm -f d3fend-full.owl
	rm -f build/*

install-deps:
	mkdir -p bin
	curl https://d3fend.pages.mitre.org/deps/robot/robot > bin/robot
	chmod +x bin/robot
	curl https://d3fend.pages.mitre.org/deps/robot/robot.jar > bin/robot.jar

# See also how to configure one's own checks and labels for checks for report:
#   http://robot.obolibrary.org/report#labels
#   http://robot.obolibrary.org/report_queries/
# 
# A copy of robot's default_profile.txt extracted from robot.jar as convenient reference.
# The report target is currently coded to not fail as some errors are not blockers yet.
report: ## Generate d3fend-full-robot-report.txt on ontology source issues
	./bin/robot report -i d3fend-full.owl --profile custom-report-profile.txt --fail-on none > robot-report.txt

robot-res-as-prop: ## Extracts and translates just restrictions -> object property assertions
	./bin/robot query --input d3fend-webprotege.owl \
		--query restrictions-as-objectproperties.rq build/d3fend-res-as-prop.owl

robot: robot-res-as-prop ## Adds in object property assertions for class property restrictions
	./bin/robot merge --input d3fend-webprotege.owl \
		--input build/d3fend-res-as-prop.owl \
		--output build/d3fend-robot.owl

builddir:
	mkdir -p build/

make-techniques-table-and-deploy: # Broken out for non-deploy builds (and esp. for ~/MITRE.crt unavail.)
	SSL_CERT_FILE=~/MITRE.crt pipenv run python makecsv.py # TODO: refactor cert out of relative home/~?

build: 	builddir robot filter-architecture-MIREOT ## npm run build and move to public folder
	cp build/d3fend-robot.owl d3fend-full.owl  # TODO refactor
	pipenv run python3 process.py

filter-architecture-star: ## Requires termfile-architecture.txt for extracted classes
	./bin/robot extract --method STAR \
		--input d3fend-webprotege.owl \
		--term-file termfile-architecture.txt \
		--output d3fend-architecture.owl

filter-architecture-MIREOT:
	./bin/robot extract --method MIREOT \
		--input d3fend-webprotege.owl \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#NetworkNode" \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#Application" \
		--output d3fend-architecture.owl

all: build make-techniques-table-and-deploy # build & deploy

help: ##print out this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help
