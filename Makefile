SHELL=/bin/bash

clean: ## cleans all build artifacts
	rm -rf build/
	rm -rf dist/
	rm -f reports/*

install-system-deps:
	yum install make -y

install-python-deps:
	pipenv install

bindir:
	mkdir -p bin

bin/robot.jar: bindir
	curl https://d3fend.pages.mitre.org/deps/robot/robot > bin/robot
	chmod +x bin/robot
	curl https://d3fend.pages.mitre.org/deps/robot/robot.jar > bin/robot.jar

install-deps: install-python-deps bin/robot.jar ## install software deps

download-attack:
	mkdir data
	cd data; wget https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-10.0.json

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

# Note: At present some definitions are d3f:definition; most are defacto rdfs:comment
reports/missing-d3fend-definition-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/missing-d3fend-definition-profile.txt \
		--fail-on none > reports/missing-d3fend-definition-report.txt

# Regression test, should not happen again.
reports/bogus-direct-subclassing-of-tactic-technique-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/bogus-direct-subclassing-of-tactic-technique-profile.txt \
		--fail-on ERROR > reports/bogus-direct-subclassing-of-tactic-technique-report.txt

reports/missing-attack-id-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/missing-attack-id-profile.txt \
		--fail-on none > reports/missing-attack-id-report.txt

reports/inconsistent-iri-report.txt:	build/d3fend-full.owl
	./bin/robot report -i build/d3fend-full.owl \
		--profile src/queries/inconsistent-iri-profile.txt \
		--fail-on none > reports/inconsistent-iri-report.txt

reports/unallowed-thing-report.txt: reportsdir build/d3fend-public.owl
	./bin/robot report -i build/d3fend-public.owl \
		--profile src/queries/unallowed-thing-profile.txt \
		--fail-on ERROR > reports/unallowed-thing-report.txt

reports/missing-off-tech-artifacts-report.txt:	build/d3fend-public.owl
#	TODO robot bug prevents this ; issue #86
#	./bin/robot report -i build/d3fend-public.owl \
#		--profile src/queries/missing-off-tech-artifacts-profile.txt \
#		--fail-on none > reports/missing-off-tech-artifacts-report.txt
	./bin/robot query --format tsv -i build/d3fend-public.owl --query src/queries/missing-off-tech-artifacts.rq reports/missing-off-tech-artifacts-report.txt

## Example robot conversion. ROBOT not used for this for build as it doesn't support JSON-LD serialization.
#robot-to-ttl:	build/d3fend-with-header.owl # Convert from .owl to .ttl format (or parse post add-header breaks! (workaround and .ttl cleaner anyway)
#	./bin/robot convert --input build/d3fend-with-header.owl -output build/d3fend-with-header.ttl

builddir:
	mkdir -p build

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

build/d3fend-with-header.owl:	src/ontology/d3fend-webprotege.owl build/d3fend-prefixes.json
	./bin/robot annotate --input src/ontology/d3fend-webprotege.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--ontology-iri "http://d3fend.mitre.org/ontologies/d3fend.owl" \
		--version-iri "http://d3fend.mitre.org/ontologies/d3fend/0.9.2/d3fend.owl" \
		--annotation dcterms:license "MIT" \
		--annotation dcterms:description "D3FEND is a framework which encodes a countermeasure knowledge base as a knowledge graph. The graph contains the types and relations that define key concepts in the cybersecurity countermeasure domain and the relations necessary to link those concepts to each other. Each of these concepts and relations are linked to references in the cybersecurity literature." \
		--annotation dcterms:title "D3FEND™ - A knowledge graph of cybersecurity countermeasures" \
		--annotation rdfs:comment "Use of the D3FEND Knowledge Graph, and the associated references from this ontology are subject to the Terms of Use. D3FEND is funded by the National Security Agency (NSA) Cybersecurity Directorate and managed by the National Security Engineering Center (NSEC) which is operated by The MITRE Corporation. D3FEND™ and the D3FEND logo are trademarks of The MITRE Corporation. This software was produced for the U.S. Government under Basic Contract No. W56KGU-18-D0004, and is subject to the Rights in Noncommercial Computer Sotware and Noncommercial Computer Software Documentation Clause 252.227-7014 (FEB 2012) Copyright 2021 The MITRE Corporation." \
		--output build/d3fend-with-header.owl
#		--prefixes d3fend-prefixes.json \ # This use of prefixes context not working with ROBOT as desired for annotate, so adding d3f with --add-prefix instead

build/d3fend-with-links.owl:	build/d3fend-with-header.owl ## converts d3f:has-link xsd:string to xsd:anyURI and fixes WebProtege ontology IRI to d3fend.mitre.org path.
	./bin/robot query --input build/d3fend-with-header.owl \
		--update src/queries/make-has-links-anyURI.rq \
		--output build/d3fend-with-links.owl

build/d3fend-trimmed-literals.owl:	build/d3fend-with-links.owl
	./bin/robot query --input build/d3fend-with-links.owl \
		--update src/queries/trimming.rq \
		--output build/d3fend-trimmed-literals.owl

build/d3fend-res-as-prop.owl:	build/d3fend-trimmed-literals.owl ## Extracts and translates just restrictions -> object property assertions
	./bin/robot query --input build/d3fend-trimmed-literals.owl \
		--query src/queries/restrictions-as-objectproperties.rq build/d3fend-res-as-prop.owl

build/d3fend-full.owl:	build/d3fend-res-as-prop.owl build/d3fend-trimmed-literals.owl ## Adds in object property assertions for class property restrictions
	./bin/robot merge --input build/d3fend-trimmed-literals.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--input build/d3fend-res-as-prop.owl \
		--output build/d3fend-full.owl

# NOTE: The hermit reasoner in Protege makes inferences as expected,
# but [AFAICT, in preliminary try] it did not pick up on transitive
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

# Must come before build/d3fend-public-no-private-annotations.owl because d3f:draft is a private annotation!
build/d3fend-public-no-draft-kb-entries.owl:	build/d3fend-full.owl
	./bin/robot remove --input build/d3fend-full.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--select "d3f:draft='true'^^xsd:boolean" \
	        --output build/d3fend-public-no-draft-kb-entries.owl

build/d3fend-public-no-private-annotations.owl: 	build/d3fend-public-no-draft-kb-entries.owl
	./bin/robot remove --input build/d3fend-public-no-draft-kb-entries.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--term d3f:d3fend-private-annotation \
		--select "self descendants instances" \
	        --output build/d3fend-public-no-private-annotations.owl

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

build/d3fend.csv: ## Broken out for non-deploy builds (and esp. for ~/MITRE.crt unavail.)
	SSL_CERT_FILE=~/MITRE.crt pipenv run python src/util/makecsv.py # TODO: refactor cert out of relative home/~?

build/d3fend-architecture.owl:	build/d3fend-full.owl
	./bin/robot extract --method MIREOT \
		--input build/d3fend-full.owl \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#NetworkNode" \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#Application" \
		--output build/d3fend-architecture.owl

build/d3fend-public-mapped.owl: build/d3fend-public.owl
	./bin/robot merge --include-annotations true --input src/ontology/mappings/d3fend-ontology-mappings.ttl --input build/d3fend-public.owl --output build/d3fend-public-mapped.owl

build: 	builddir build/d3fend-full.owl build/d3fend-public.owl build/d3fend-public-mapped.owl reports/unallowed-thing-report.txt build/d3fend-architecture.owl build/d3fend.csv ## run build and move to public folder, used to create output files, including JSON-LD, since robot doesn't support serializing to JSON-LD
	pipenv run python3 src/util/build.py # expects a build/d3fend-public.owl file

reportsdir:
	mkdir -p reports/

reports:	reportsdir reports/default-robot-report.txt reports/missing-d3fend-definition-report.txt reports/bogus-direct-subclassing-of-tactic-technique-report.txt reports/missing-attack-id-report.txt reports/inconsistent-iri-report.txt reports/missing-off-tech-artifacts-report.txt ## Generates all reports for ontology quality checks

robot:	add-header reports fix-has-links fix-whitespace-literals res-as-prop merge-prop public

distdir:
	mkdir -p dist/public dist/private


test-load-owl:	reportsdir build/d3fend-public.owl ## Used to check d3fend.owl file as parseable and useable for DL profile.
	./bin/robot validate-profile --prefixes build/d3fend-prefixes.json --profile DL --input build/d3fend-public.owl --output reports/owl-validation.txt > reports/owl-validation-stdout.txt

test-load-ttl:	reportsdir build/d3fend-public.ttl ## Used to check d3fend.ttl file as parseable and useable for DL profile.
	./bin/robot validate-profile --profile DL --input build/d3fend-public.ttl --output reports/ttl-validation.txt > reports/ttl-validation-stdout.txt

test-load-json:	reportsdir ## Used to check d3fend.json (JSON-LD) file as parseable and useable for DL profile.
#	./bin/robot validate-profile --profile DL --input d3fend.json --output reports/json-validation.txt # JSON-LD serialized by RDFlib not read by ROBOT or Protege
	pipenv run python3 src/tests/test_load_json.py build/d3fend-public.json
	echo "RDFLib parsed d3fend.json successfully" > reports/json-validation.txt

test-load-full:	reportsdir ## Used to check d3fend-full.owl as parseable and useable for DL profile.
	./bin/robot validate-profile --profile DL --input build/d3fend-full.owl --output reports/full-validation.txt > reports/full-validation-stdout.txt

test:	test-load-owl test-load-ttl test-load-json test-load-full ## Checks all ontology build files as parseable and DL-compatible.

dist: build distdir
	cp build/d3fend-full.owl dist/private/d3fend-full.owl
	cp build/d3fend-public.owl dist/public/d3fend.owl
	cp build/d3fend-public-mapped.owl dist/public/d3fend-mapped.owl
	cp build/d3fend-public.ttl dist/public/d3fend.ttl
	cp build/d3fend-public.json dist/public/d3fend.json
	cp build/d3fend.csv dist/public/d3fend.csv
	cp build/d3fend-architecture.owl dist/public/d3fend-architecture.owl

all: build test dist ## build all, check for unallowed content, and test load files

print-new-techniques:
	diff -y -W 500 dist/public/d3fend.csv <(curl -s https://d3fend.mitre.org/ontologies/d3fend.csv) | grep \< | sed  "s/\<//g"

help: ##print out this message
	@grep -E '^[^@]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help
