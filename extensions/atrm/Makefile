MAKEFLAGS += --silent

SHELL=/bin/bash

ATRM_VERSION :=0.1
ATRM_RELEASE_DATE :="2024-03-07T00:00:00.000Z"


# define standard colors
ifneq (,$(findstring xterm,${TERM}))
	BLACK        := $(shell tput -Txterm setaf 0)
	RED          := $(shell tput -Txterm setaf 1)
	GREEN        := $(shell tput -Txterm setaf 2)
	YELLOW       := $(shell tput -Txterm setaf 3)
	LIGHTPURPLE  := $(shell tput -Txterm setaf 4)
	PURPLE       := $(shell tput -Txterm setaf 5)
	BLUE         := $(shell tput -Txterm setaf 6)
	WHITE        := $(shell tput -Txterm setaf 7)
	RESET := $(shell tput -Txterm sgr0)
else
	BLACK        := ""
	RED          := ""
	GREEN        := ""
	YELLOW       := ""
	LIGHTPURPLE  := ""
	PURPLE       := ""
	BLUE         := ""
	WHITE        := ""
	RESET        := ""
endif


START = echo "${BLUE}$@ started ${RESET}"
END = echo "${GREEN}$@ done ${RESET}"
FAIL = echo "${RED}$@ failed ${RESET}"

BUILD_DIR = extensions/atrm/build

clean: ## cleans all build artifacts
	echo "Cleaning all ATRM build artifacts..."
	rm -rf build/
	rm -rf atrm-stix-data/
	$(END)

install-python-deps:
	pipenv install
	$(END)

install-deps: install-python-deps ## install software deps
	$(END)

builddir:
	mkdir -p build
	$(END)

atrm-stix-data/build/atrm_attack_compatible.json:
	echo Cloning ATRM STIX repository
	git clone https://github.com/Security-Experts-Community/atrm-stix-data.git
	$(END)

build/atrm-ontology.ttl: install-python-deps atrm-stix-data/build/atrm_attack_compatible.json builddir
	echo Building ATRM
	pipenv run python3 ./atrm-mapping.py
	$(END)

build/atrm-with-header.ttl:	build/atrm-ontology.ttl
	cd ../../; \
	./bin/robot annotate --input ${BUILD_DIR}/atrm-ontology.ttl \
		--version-iri "http://sec-kg.org/ontologies/atrm/${atrm_VERSION}/atrm.ttl" \
		--typed-annotation "http://sec-kg.org/ontologies/atrm#release-date" ${atrm_RELEASE_DATE} xsd:dateTime \
		--annotation owl:versionInfo ${atrm_VERSION} \
		--output ${BUILD_DIR}/atrm-with-header.ttl
	$(END)

build/atrm-with-links.ttl:	build/atrm-with-header.ttl ## converts d3f:has-link xsd:string to xsd:anyURI and fixes WebProtege ontology IRI to d3fend.mitre.org path.
	cd ../../; \
	./bin/robot query --input ${BUILD_DIR}/atrm-with-header.ttl \
		--update src/queries/make-has-links-anyURI.rq \
		--output ${BUILD_DIR}/atrm-with-links.ttl
	$(END)

build/atrm.ttl:	build/atrm-with-links.ttl
	cd ../../; \
	./bin/robot query --input ${BUILD_DIR}/atrm-with-links.ttl \
		--update src/queries/trimming.rq \
		--output ${BUILD_DIR}/atrm.ttl
	$(END)

build: build/atrm-ontology.ttl
	$(END)

all: build
	$(END)

help: ##print out this message
	@grep -E '^[^@]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

format: ## Format ttl to canonical, stable format for effective diffing (accomplished before any commits)
	pipenv run ttlfmt build/ms-matrices-ontology.ttl

# requires https://pre-commit.com/#install
pre-commit-install:
	pre-commit install

pre-commit:
	pre-commit run --all-files

.PHONY: all help clean build dist test robot

.DEFAULT_GOAL := help
