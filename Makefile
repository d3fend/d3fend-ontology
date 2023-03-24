MAKEFLAGS += --silent

SHELL=/bin/bash

D3FEND_VERSION :=0.12.0-BETA-2
D3FEND_RELEASE_DATE :="2023-03-21T00:00:00.000Z"

JENA_VERSION := 4.5.0

JENA_PATH := "bin/jena/apache-jena-${JENA_VERSION}/bin"

ROBOT_URL := "https://github.com/ontodev/robot/releases/download/v1.9.0/robot.jar"

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

DB_LOCAL := "http://127.0.0.1:9899"
DB_PROD := "http://PRODUCTIONSERVER.local:9899"
DB_REST_PATH := "/blazegraph/namespace/d3fend/sparql"
DB_REST_PATH_INF := "/blazegraph/namespace/d3fend_inf/sparql"
DB_REST_PATH_BD := "/bigdata/namespace/d3fend/sparql"
DB_REST_PATH_BD_INF := "/bigdata/namespace/d3fend_inf/sparql"
DB_REST_PATH_TEST := "/bigdata/namespace/d3fend-test/sparql"

db-delete-local:
	@curl -s -o /dev/null -w "deleted ${DB_LOCAL}${DB_REST_PATH} %{http_code}\n"  ${DB_LOCAL}${DB_REST_PATH} --data-urlencode "update=DROP ALL;"
	@curl -s -o /dev/null -w "deleted ${DB_LOCAL}${DB_REST_PATH_INF} %{http_code}\n" ${DB_LOCAL}${DB_REST_PATH_INF} --data-urlencode "update=DROP ALL;"

db-delete-prod:
	@curl -s -o /dev/null -w "deleted ${DB_PROD}${DB_REST_PATH} %{http_code}\n"  ${DB_PROD}${DB_REST_PATH_BD} --data-urlencode "update=DROP ALL;"
	@curl -s -o /dev/null -w "deleted ${DB_PROD}${DB_REST_PATH_BD_INF} %{http_code}\n" ${DB_PROD}${DB_REST_PATH_BD_INF} --data-urlencode "update=DROP ALL;"

db-load-local:
	@curl -s -o /dev/null -w "loaded ${DB_LOCAL}${DB_REST_PATH} %{http_code}\n" -H 'Content-Type:application/x-turtle'  -X POST --upload-file dist/public/d3fend.ttl ${DB_LOCAL}${DB_REST_PATH}
	@curl -s -o /dev/null -w "loaded ${DB_LOCAL}${DB_REST_PATH_INF} %{http_code}\n" -H 'Content-Type:application/x-turtle'  -X POST --upload-file dist/public/d3fend.ttl ${DB_LOCAL}${DB_REST_PATH_INF}

db-load-prod:
	@curl -s -o /dev/null -w "loaded ${DB_PROD}${DB_REST_PATH} %{http_code}\n" -H 'Content-Type:application/x-turtle'  -X POST --upload-file dist/public/d3fend.ttl ${DB_PROD}${DB_REST_PATH_BD}
	@curl -s -o /dev/null -w "loaded ${DB_PROD}${DB_REST_PATH_INF} %{http_code}\n" -H 'Content-Type:application/x-turtle'  -X POST --upload-file dist/public/d3fend.ttl ${DB_PROD}${DB_REST_PATH_BD_INF}

db-sync-prod: db-delete-prod db-load-prod

db-sync-local: db-delete-local db-load-local

db-load-prod-restore:
	curl -D- -H 'Content-Type:application/x-turtle' -v -X POST --upload-file "BACKUPFILE".ttl ${DB_PROD}${DB_REST_PATH_BD}
	@curl -s -o /dev/null -w "loaded ${DB_PROD}${DB_REST_PATH} %{http_code}\n" -H 'Content-Type:application/x-turtle'  -X POST --upload-file "BACKUPFILE".ttl ${DB_PROD}${DB_REST_PATH}
	@curl -s -o /dev/null -w "loaded ${DB_PROD}${DB_REST_PATH_INF} %{http_code}\n" -H 'Content-Type:application/x-turtle'  -X POST --upload-file "BACKUPFILE".ttl ${DB_PROD}${DB_REST_PATH_INF}

# run make-onto again at end to rebuild the csv with latest data
db-sync-all: db-delete-local db-load-local db-delete-prod db-load-prod ## sync local and prod dbs with current ontology



clean: ## cleans all build artifacts
	rm -rf build/
	rm -rf dist/
	rm -f reports/*
	$(END)

install-system-deps:
	yum install make -y
	$(END)

install-python-deps:
	pipenv install
	$(END)

bindir:
	mkdir -p bin bin/.library
	$(END)

bin/jena: bindir
	mkdir -p bin/jena
	curl https://archive.apache.org/dist/jena/binaries/apache-jena-${JENA_VERSION}.tar.gz | tar xzf - -C bin/jena
	$(END)

bin/robot.jar: bindir
	echo -ne '#!/bin/bash\njava -jar bin/robot.jar "$$@"\n' > bin/robot && chmod +x bin/robot
	curl -L $(ROBOT_URL) > bin/robot.jar
	$(END)

install-deps: install-python-deps bin/robot.jar bin/jena ## install software deps
	$(END)

download-attack:
	mkdir -p data
	cd data; wget https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-11.2.json
	$(END)

update-attack:
	bash src/util/update_attack.sh
	$(END)

# See also how to configure one's own checks and labels for checks for report:
#   http://robot.obolibrary.org/report#labels
#   http://robot.obolibrary.org/report_queries/
#
# A copy of robot's default_profile.txt extracted from robot.jar and
# placed in src/queries/ as convenient reference.  The report target is
# currently coded to not fail as some errors are not blockers
# yet. These reports are done immediately after adding ontology header
# annotations to output from Web Protege.
reports/default-robot-report.txt:	build/d3fend-full.owl ## Generate d3fend-full-robot-report.txt on ontology source issues
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/custom-report-profile.txt \
		--fail-on none > reports/default-robot-report.txt
	$(END)

# Note: At present some definitions are d3f:definition; most are defacto rdfs:comment
reports/missing-d3fend-definition-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/missing-d3fend-definition-profile.txt \
		--fail-on none > reports/missing-d3fend-definition-report.txt
	$(END)

# Regression test, should not happen again.
reports/bogus-direct-subclassing-of-tactic-technique-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/bogus-direct-subclassing-of-tactic-technique-profile.txt \
		--fail-on ERROR > reports/bogus-direct-subclassing-of-tactic-technique-report.txt
	$(END)

reports/missing-attack-id-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/missing-attack-id-profile.txt \
		--fail-on none > reports/missing-attack-id-report.txt
	$(END)

reports/inconsistent-iri-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/inconsistent-iri-profile.txt \
		--fail-on none > reports/inconsistent-iri-report.txt
	$(END)

reports/unallowed-thing-report.txt: reportsdir build/d3fend-public.owl
	./bin/robot report -i build/d3fend-public.owl \
		--profile src/queries/unallowed-thing-profile.txt \
		--fail-on ERROR > reports/unallowed-thing-report.txt
	$(END)

reports/missing-off-tech-artifacts-report.txt:	build/d3fend-public.owl
	./bin/robot query --format tsv -i build/d3fend-public.owl --query src/queries/missing-off-tech-artifacts.rq reports/missing-off-tech-artifacts-report.txt
	$(END)

builddir:
	mkdir -p build
	$(END)

# TODO, we may be able to remove this target
build/d3fend-prefixes.json: builddir ## create d3fend-specific prefix file for use with ROBOT
	./bin/robot --noprefixes \
		--add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#" \
		--add-prefix "rdfs: http://www.w3.org/2000/01/rdf-schema#" \
		--add-prefix "xsd: http://www.w3.org/2001/XMLSchema#" \
		--add-prefix "owl: http://www.w3.org/2002/07/owl#"  \
		--add-prefix "skos: http://www.w3.org/2004/02/skos/core#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		export-prefixes --output build/d3fend-prefixes.json
	$(END)

build/d3fend-with-header.owl:	src/ontology/d3fend-protege.ttl
	./bin/robot annotate --input src/ontology/d3fend-protege.ttl \
		--version-iri "http://d3fend.mitre.org/ontologies/d3fend/${D3FEND_VERSION}/d3fend.owl" \
		--typed-annotation "http://d3fend.mitre.org/ontologies/d3fend.owl#release-date" ${D3FEND_RELEASE_DATE} xsd:dateTime \
		--annotation owl:versionInfo ${D3FEND_VERSION} \
		--output build/d3fend-with-header.owl
	$(END)

build/d3fend-with-links.owl:	build/d3fend-with-header.owl ## converts d3f:has-link xsd:string to xsd:anyURI and fixes WebProtege ontology IRI to d3fend.mitre.org path.
	./bin/robot query --input build/d3fend-with-header.owl \
		--update src/queries/make-has-links-anyURI.rq \
		--output build/d3fend-with-links.owl
	$(END)

build/d3fend-trimmed-literals.owl:	build/d3fend-with-links.owl
	./bin/robot query --input build/d3fend-with-links.owl \
		--update src/queries/trimming.rq \
		--output build/d3fend-trimmed-literals.owl
	$(END)

build/d3fend-res-as-prop.owl:	build/d3fend-trimmed-literals.owl ## Extracts and translates just restrictions -> object property assertions
	./bin/robot query --input build/d3fend-trimmed-literals.owl \
		--query src/queries/restrictions-as-objectproperties.rq build/d3fend-res-as-prop.owl
	$(END)

build/d3fend-full.owl:	build/d3fend-res-as-prop.owl build/d3fend-trimmed-literals.owl ## Adds in object property assertions for class property restrictions
	./bin/robot merge --input build/d3fend-trimmed-literals.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--input build/d3fend-res-as-prop.owl \
		--output build/d3fend-full.owl
	$(END)

# NOTE: The hermit reasoner in Protege makes inferences as expected,
# but [in preliminary try] it did not pick up on transitive
# inferences nor modifies-part AFAICT.  Deferred until after first
# public release of D3FEND.
#
# TODO When ready, add this back as final pre-public step and rewicker
# filenames to establish build chain dependency/sequencing.
#
# build/d3fend-materialized.owl:	build/d3fend-full.owl
# 	./bin/robot reason --reasoner hermit \
# 		--annotate-inferred-axioms true \
# 		--input build/d3fend-full.owl \
# 	        --output build/d3fend-materialized.owl

# Must come before build/d3fend-public-no-private-annotations.owl because d3f:draft is a private annotation
build/d3fend-public-no-draft-kb-entries.owl:	build/d3fend-full.owl
	./bin/robot remove --input build/d3fend-full.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--select "d3f:draft='true'^^xsd:boolean" \
	        --output build/d3fend-public-no-draft-kb-entries.owl
	$(END)

build/d3fend-public-no-private-annotations.owl: 	build/d3fend-public-no-draft-kb-entries.owl
	./bin/robot remove --input build/d3fend-public-no-draft-kb-entries.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--term d3f:d3fend-private-annotation \
		--select "self descendants instances" \
	        --output build/d3fend-public-no-private-annotations.owl
	$(END)

build/d3fend-public.owl:	build/d3fend-public-no-private-annotations.owl
	./bin/robot remove --input build/d3fend-public-no-private-annotations.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--term d3f:AnalysisCitation \
		--term d3f:AssertionConfidence \
		--term d3f:D3FENDAnalysisThing \
		--term d3f:D3FENDAnalysis \
		--term d3f:D3FENDAnalyst \
		--term d3f:FormFactor \
		--term d3f:License \
		--term d3f:OSSupport \
		--term d3f:Product \
		--term d3f:ProductDeveloper \
		--term d3f:SupportLevel \
		--term d3f:TechniqueAssertion \
		--select instances \
	        --output build/d3fend-public.owl
	$(END)

build/d3fend.csv: build/d3fend-public.owl ## make D3FEND csv, not part of build or all targets
	SSL_CERT_FILE=~/MITRE.crt pipenv run python src/util/makecsv.py
	$(END)

build/d3fend-architecture.owl:	build/d3fend-full.owl
	./bin/robot extract --method MIREOT \
		--input build/d3fend-full.owl \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#NetworkNode" \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#Application" \
		--output build/d3fend-architecture.owl
	$(END)

build/d3fend-public-mapped.owl: build/d3fend-public.owl
	./bin/robot merge --include-annotations true --input src/ontology/mappings/d3fend-ontology-mappings.ttl --input build/d3fend-public.owl --output build/d3fend-public-mapped.owl
	$(END)

build/d3fend-public.ttl: build/d3fend-public.owl
	./bin/robot convert --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" --input build/d3fend-public.owl --output build/d3fend-public.ttl

build/d3fend-inferred-relationships.csv:
	./bin/robot query --format csv -i build/d3fend-public.owl --query src/queries/def-to-off-with-prop-asserts-all.rq build/d3fend-inferred-relationships.csv
	$(END)

build/cci-to-d3fend-mapping.ttl: build/d3fend-public.owl
	pipenv run python extensions/cci/create_cci_mappings.py
	$(END)

build/sp800-53r5-control-to-d3fend-mapping.ttl: build/d3fend-public.owl
	pipenv run python extensions/nist/create_nist_mappings.py
	$(END)

build/extensions: build/d3fend-public.ttl build/cci-to-d3fend-mapping.ttl build/sp800-53r5-control-to-d3fend-mapping.ttl ## build D3FEND Extensions
	cat build/d3fend-public.ttl > build/d3fend-public-with-controls.ttl
	cat build/sp800-53r5-control-to-d3fend-mapping.ttl >> build/d3fend-public-with-controls.ttl
	cat build/cci-to-d3fend-mapping.ttl >> build/d3fend-public-with-controls.ttl
	pipenv run ttlfmt build/d3fend-public-with-controls.ttl
	./bin/robot convert --input build/d3fend-public-with-controls.ttl --output build/d3fend-public-with-controls.owl
	$(END)

build/ontology: builddir build/d3fend-full.owl build/d3fend-public.owl build/d3fend-public-mapped.owl reports/unallowed-thing-report.txt build/d3fend-architecture.owl build/d3fend-prefixes.json build/extensions ## run build and move to public folder, used to create output files, including JSON-LD, since robot doesn't support serializing to JSON-LD
	$(END)

build: build/ontology # build the D3FEND Ontology and Extensions
	pipenv run python3 src/util/build.py extensions # expects a build/d3fend-public-with-controls.owl file
	$(END)

reportsdir:
	mkdir -p reports/
	$(END)

reports:	reportsdir reports/default-robot-report.txt reports/missing-d3fend-definition-report.txt reports/bogus-direct-subclassing-of-tactic-technique-report.txt reports/missing-attack-id-report.txt reports/inconsistent-iri-report.txt reports/missing-off-tech-artifacts-report.txt ## Generates all reports for ontology quality checks
	$(END)

distdir:
	mkdir -p dist/public dist/private
	$(END)

test-load-owl:	reportsdir build/d3fend-public.owl ## Used to check d3fend.owl file as parseable and useable for DL profile.
	./bin/robot validate-profile --profile DL --input build/d3fend-public-with-controls.owl --output reports/test-owl-validation.txt > reports/test-owl-validation-stdout.txt
	$(END)

test-load-ttl:	reportsdir build/d3fend-public.ttl ## Used to check d3fend.ttl file as parseable and useable for DL profile.
	./bin/robot validate-profile --profile DL --input build/d3fend-public-with-controls.ttl --output reports/test-ttl-validation.txt > reports/test-ttl-validation-stdout.txt
	$(END)

test-load-json:	reportsdir ## Used to check d3fend.json (JSON-LD) file as parseable and useable for DL profile.
#	./bin/robot validate-profile --profile DL --input d3fend.json --output reports/json-validation.txt # JSON-LD serialized by RDFlib not read by ROBOT or Protege
	@pipenv run python3 src/tests/test_load_json.py build/d3fend-public-with-controls.json > reports/test-load-json.txt
	$(END)

test-load-full:	reportsdir ## Used to check d3fend-full.owl as parseable and useable for DL profile.
	./bin/robot validate-profile --profile DL --input build/d3fend-full.owl --output reports/test-owl-validation.txt > reports/test-owl-validation-stdout.txt
	$(END)

test-jena: reportsdir ## Used to check d3fend-full.owl as parseable and useable for jena libraries
	@${JENA_PATH}/riot --validate build/d3fend-public-with-controls.owl > reports/test-owl-jena-validation.txt
	$(END)

test-reasoner:
	./bin/robot reason --reasoner ELK --input build/d3fend-public-with-controls.ttl -D reports/test-reasoner-results.ttl

test:	test-load-owl test-load-ttl test-load-json test-load-full test-jena test-reasoner ## Checks all ontology build files as parseable and DL-compatible.
	$(END)

dist: distdir
	cp build/d3fend-full.owl dist/private/d3fend-full.owl
	cp build/d3fend-public-mapped.owl dist/public/d3fend-mapped.owl
	cp build/d3fend-public-with-controls.ttl dist/public/d3fend.ttl # For now, roll in the CCI & NIST controls extensions to base .ttl release
	cp build/d3fend-public-with-controls.owl dist/public/d3fend.owl # For now, roll in the CCI & NIST controls extensions to base .owl release
	cp build/d3fend-public-with-controls.json dist/public/d3fend.json
	@cp build/d3fend.csv dist/public/d3fend.csv ||  echo "${RED}WARNING: build/d3fend.csv not found to include in dist. Manually run: ${YELLOW} make build/d3fend.csv ${RESET} ${RESET}"
	cp build/d3fend-architecture.owl dist/public/d3fend-architecture.owl
	chmod 644 dist/public/d3fend.ttl dist/public/d3fend.owl
	$(END)

all: build build/d3fend.csv extensions dist test  ## build all, check for unallowed content, and test load files
	$(END)

print-new-techniques: build/d3fend.csv ## compare local build against current public version
	diff -y -W 500 build/d3fend.csv <(curl -s https://d3fend.mitre.org/ontologies/d3fend.csv) | grep \< | sed  "s/\<//g"
	$(END)

help: ##print out this message
	@grep -E '^[^@]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

format: ## Format ttl to canonical, stable format for effective diffing (accomplished before any commits)
	pipenv run ttlfmt src/ontology/d3fend-protege.ttl

# requires https://pre-commit.com/#install
pre-commit-install:
	pre-commit install

pre-commit:
	pre-commit run --all-files


.PHONY: all help clean build dist test robot

.DEFAULT_GOAL := help
