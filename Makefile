SHELL ?= /usr/local/bin/bash

clean:
	rm -f d3fend.*
	rm -f d3fend-webprotege.json
	rm -f build/d3fend.*
	rm -f d3fend-architecture*
	rm -f d3fend-full.owl
	rm -f build/*
	rm -f reports/*

install-deps:
	mkdir -p bin
	curl https://d3fend.pages.mitre.org/deps/robot/robot > bin/robot
	chmod +x bin/robot
	curl https://d3fend.pages.mitre.org/deps/robot/robot.jar > bin/robot.jar

# See also how to configure one's own checks and labels for checks for report:
#   http://robot.obolibrary.org/report#labels
#   http://robot.obolibrary.org/report_queries/
# 
# A copy of robot's default_profile.txt extracted from robot.jar and
# placed in queries/ as convenient reference.  The report target is
# currently coded to not fail as some errors are not blockers
# yet. These reports are done immediately after adding ontology header
# annotations to output from Web Protege.
general-report:	build/d3fend-with-header.owl ## Generate d3fend-full-robot-report.txt on ontology source issues
	./bin/robot report -i build/d3fend-with-header.owl \
		--profile queries/custom-report-profile.txt \
		--fail-on none > reports/default-robot-report.txt

missing-def-tech-comment-report:	build/d3fend-with-header.owl
	./bin/robot report -i build/d3fend-with-header.owl \
		--profile queries/missing-def-tech-comment-profile.txt \
		--fail-on none > reports/missing-def-tech-comment-report.txt

missing-dao-comment-report:	build/d3fend-with-header.owl # 
	./bin/robot report -i build/d3fend-with-header.owl \
		--profile queries/missing-dao-comment-profile.txt \
		--fail-on none > reports/missing-dao-comment-report.txt

## Example robot conversion. ROBOT not used for this for build as it doesn't support JSON-LD serialization.
#robot-to-ttl:	build/d3fend-with-header.owl # Convert from .owl to .ttl format (or parse post add-header breaks! (workaround and .ttl cleaner anyway)
#	./bin/robot convert --input build/d3fend-with-header.owl -output build/d3fend-with-header.ttl

#robot-rename:	build/d3fend-with-header.owl
#	./bin/robot -vvv rename --input build/d3fend-with-header.owl \
#		--prefix-mappings prefix-mappings.tsv \
#		--output build/d3fend-renamed.owl
#	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \

d3fend-prefixes.json: ## create d3fend-specific prefix file for use with ROBOT
	./bin/robot --noprefixes \
		--add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#" \
		--add-prefix "rdfs: http://www.w3.org/2000/01/rdf-schema#" \
		--add-prefix "xsd: http://www.w3.org/2001/XMLSchema#" \
		--add-prefix "owl: http://www.w3.org/2002/07/owl#"  \
		--add-prefix "skos: http://www.w3.org/2004/02/skos/core#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		export-prefixes --output d3fend-prefixes.json

build/d3fend-with-header.owl:	d3fend-webprotege.owl d3fend-prefixes.json
	./bin/robot annotate --input d3fend-webprotege.owl \
	        --add-prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
		--add-prefix "dcterms: http://purl.org/dc/terms/" \
		--ontology-iri "http://d3fend.mitre.org/ontologies/d3fend.owl" \
		--version-iri "http://d3fend.mitre.org/ontologies/d3fend/0.9.2/d3fend.owl" \
		--annotation dcterms:license "MIT" \
		--annotation dcterms:description "D3FEND is a framework which encodes a countermeasure knowledge base as a knowledge graph. The graph contains the types and relations that define key concepts in the cybersecurity countermeasure domain and the relations necessary to link those concepts to each other. Each of these concepts and relations are linked to references in the cybersecurity literature." \
		--annotation dcterms:title "D3FEND™ - A knowledge graph of cybersecurity" \
		--annotation rdfs:comment "Use of the D3FEND Knowledge Graph, and the associated references from this ontology are subject to the Terms of Use. D3FEND is funded by the National Security Agency (NSA) Cybersecurity Directorate and manage by the National Security Engineering Center (NSEC) whcih is operated by The MITRE Corporation. D3FEND™ and the D3FEND logo are trademarks of The MITRE Corporation. This software was produced for the U.S. Government under Basic Contract No. W56KGU-18-D0004, and is subject to the Rights in Noncommercial Computer Sotware and Noncommercial Computer Software Documentation Clause 252.227-7014 (FEB 2012) Copyright 2021 The MITRE Corporation." \
		--output build/d3fend-with-header.owl
#		--prefixes d3fend-prefixes.json \ # This use of prefixes context not working with ROBOT as desired for annotate, so adding d3f with --add-prefix instead

build/d3fend-with-links.owl:	build/d3fend-with-header.owl ## converts d3f:has-link xsd:string to xsd:anyURI and fixes WebProtege ontology IRI to d3fend.mitre.org path.
	./bin/robot query --input build/d3fend-with-header.owl \
		--update queries/make-has-links-anyURI.rq \
		--output build/d3fend-with-links.owl

build/d3fend-trimmed-literals.owl:	build/d3fend-with-links.owl
	./bin/robot query --input build/d3fend-with-links.owl \
		--update queries/trimming.rq \
		--output build/d3fend-trimmed-literals.owl

build/d3fend-res-as-prop.owl:	build/d3fend-trimmed-literals.owl ## Extracts and translates just restrictions -> object property assertions
	./bin/robot query --input build/d3fend-trimmed-literals.owl \
		--query queries/restrictions-as-objectproperties.rq build/d3fend-res-as-prop.owl

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

build/d3fend-public-no-private-annotations.owl: 	build/d3fend-full.owl
	./bin/robot remove --input build/d3fend-full.owl \
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

# Got todo and comment through inheritance
#		--term d3f:todo \
#		--term d3f:comment \
# For some reason can't get rid of people by name either way.
#               --select "owl:NamedIndividual=d3f:ChrisThorpe" \
#		--term d3f:JayVora \
#		--term d3f:MichaelSmith \
#		--term d3f:ParkerGarrison \
#		--term d3f:PeterKaloroumakis \
# Trimming doesn't help
#		--trim true \

reportsdir:
	mkdir -p reports/

reports:	reportsdir general-report missing-def-tech-comment-report missing-dao-comment-report ## Generates all reports for ontology quality checks

robot:	add-header reports fix-has-links fix-whitespace-literals res-as-prop merge-prop public

builddir:
	mkdir -p build/

make-techniques-table-and-deploy: ## Broken out for non-deploy builds (and esp. for ~/MITRE.crt unavail.)
	SSL_CERT_FILE=~/MITRE.crt pipenv run python makecsv.py # TODO: refactor cert out of relative home/~?

d3fend-architecture.owl:
	./bin/robot extract --method MIREOT \
		--input d3fend-webprotege.owl \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#NetworkNode" \
		--branch-from-term "http://d3fend.mitre.org/ontologies/d3fend.owl#Application" \
		--output d3fend-architecture.owl

build: 	builddir build/d3fend-full.owl build/d3fend-public.owl d3fend-architecture.owl ## run build and move to public folder, used to create output files, including JSON-LD, since robot doesn't support serializing to JSON-LD
	pipenv run python3 process.py # expects a build/d3fend-public.owl file
	cp build/d3fend-full.owl d3fend-full.owl

# Continue make even on ROBOT fail, as it fails on bogus undeclared annotation property PROFILE VALIDATION ERROR about dcterms:{description,title,license}
test-load-owl:	reportsdir ## Used to check d3fend.owl file as parseable and useable for DL profile.
	-./bin/robot validate-profile --prefixes d3fend-prefixes.json --profile DL --input d3fend.owl --output reports/owl-validation.txt > reports/owl-validation-stdout.txt

# Continue make even on ROBOT fail, as it fails on bogus undeclared annotation property PROFILE VALIDATION ERROR about dcterms:{description,title,license}
test-load-ttl:	reportsdir ## Used to check d3fend.ttl file as parseable and useable for DL profile.
	-./bin/robot validate-profile --profile DL --input d3fend.ttl --output reports/ttl-validation.txt > reports/ttl-validation-stdout.txt

test-load-json:	reportsdir ## Used to check d3fend.json (JSON-LD) file as parseable and useable for DL profile.
#	./bin/robot validate-profile --profile DL --input d3fend.json --output reports/json-validation.txt # JSON-LD serialized by RDFlib not read by ROBOT or Protege
	pipenv run python3 test_load_json.py
	echo "RDFLib parsed d3fend.json successfully" > reports/json-validation.txt

# Continue make even on ROBOT fail, as it fails on bogus undeclared annotation property PROFILE VALIDATION ERROR about dcterms:{description,title,license}
test-load-full:	reportsdir ## Used to check d3fend-full.owl as parseable and useable for DL profile.
	-./bin/robot validate-profile --profile DL --input d3fend-full.owl --output reports/full-validation.txt > reports/full-validation-stdout.txt

test-load-files:	test-load-owl test-load-ttl test-load-json test-load-full ## Checks all ontology build files as parseable and DL-compatible.

all: clean build test-load-files make-techniques-table-and-deploy ## build & deploy as table (.csv)

help: ##print out this message
	@grep -E '^[^@]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: help

.DEFAULT_GOAL := help
