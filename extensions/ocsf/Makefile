# Variables
OCSF_DOWNLOAD_DIR := ./downloads
OCSF_VERSION := 1.4.0
OCSF_DOWNLOAD_VER=ocsf-schema-$(OCSF_VERSION)

# *MUST* have trailing space or will be cut back to just ...downloads/
BASE_IRI=file://$(shell pwd)/downloads/$(OCSF_DOWNLOAD_VER)/

# Install sparql-generate jar
install-sparql-generate:
	wget https://github.com/sparql-generate/sparql-generate/releases/download/2.1.0/sparql-generate-2.1.0.jar
	wget https://repo1.maven.org/maven2/com/jayway/jsonpath/json-path/2.9.0/json-path-2.9.0.jar

# Put in the bin/jar directory
install-deps: install-sparql-generate

# Convenience target to fetch the release name and download the archive on updates
fetch-latest-archive:
	@echo "Fetching latest release name..."
	@RELEASE_NAME=$$(gh release list --repo ocsf/ocsf-schema --limit 1 | awk '{print $$3}') && \
	echo "Latest release name: $$RELEASE_NAME" && \
	echo "Downloading archive file $$RELEASE_NAME.zip..." && \
	mkdir -p $(OCSF_DOWNLOAD_DIR) && \
	wget -q -O $(OCSF_DOWNLOAD_DIR)/$$RELEASE_NAME.zip https://github.com/ocsf/ocsf-schema/archive/$$RELEASE_NAME.zip && \
	echo "Archive downloaded to $(OCSF_DOWNLOAD_DIR)/$$RELEASE_NAME.zip" && \
	cd $(OCSF_DOWNLOAD_DIR); unzip $$RELEASE_NAME.zip

list:
	@find . -type f -name "*.ttl" | xargs -n 1 echo

# Allows ability to quickly test SPARQL-Generate fragments
test:
	java -jar sparql-generate-2.1.0.jar -q test.rqg -o test.ttl 
	pipenv run ttlfmt test.ttl
	more test.ttl

# The first target is base target and it covers any assertions that we
# choose to (or have to) make directly at the beginning and
# establishes the first output into dataset/ocsf.ttl based on the
# graph: property in the sparql-generate-conf.json file.
#
# For consideration: Have option to generate component .ttl files with
# clever Makefile switch.
# 
# NOTE: Use ttlfmt through so that the results are stable for diffs.
#
# NOTE: There might be some way to have fewer queries that are
# repeated to converge on a fixed point and handle all the partial
# matches and remove redundant generation, but instead have entirely
# sequenced the steps.
#
# NOTE: It appears you can get output to only one file, can't get -o
# to go to one and graph property to specify the default and get it
# out there too.  So we'll just build incrementally and not also
# generate the different partitions of assertions into separate files
# (if that's desired for debgging, just don't use --append-output and
# write to another file (see commented-out example for events make
# target.
#
# TODO: Figure a way to meta-generate, or iterate over some resource
# that contains all the individual files event and object class
# (.json) files in the schema directories so these don't have to be
# hand spec'd. This would be necessary to quickly move between OCSF
# schema versions so that all the things that are enumerated GENERATE
# statements to event.rqg, object.rqg, erestriction.rqg,
# orestriction.rqg that are respectively inn events.rqg, objects.rqg,
# erestrictions.rqg, and orestrictions.rqg
#
base:
	java -jar sparql-generate-2.1.0.jar -q base.rqg -o dataset/ocsf.ttl --append-output
	pipenv run ttlfmt dataset/ocsf.ttl

categories: base
	java -jar sparql-generate-2.1.0.jar -q categories.rqg -o dataset/ocsf.ttl --append-output
	pipenv run ttlfmt dataset/ocsf.ttl

## Functional to here, events
events: categories
#	java -jar sparql-generate-2.1.0.jar -q events.rqg -o events.ttl # just write new triples generated for events.rqg
	echo "Base directory for OCSF json schema->OCSF OWL in D3FEND: $(BASE_IRI)" && \
	java -jar sparql-generate-2.1.0.jar -q events.rqg -o dataset/ocsf.ttl --append-output --base $(BASE_IRI)
	pipenv run ttlfmt dataset/ocsf.ttl

# TODO continue to build up graph 
objects: categories # Not dependent on events, AFAICT
	java -jar sparql-generate-2.1.0.jar -q objects.rqg -o dataset/ocsf.ttl --append-output --base $(BASE_IRI)
	pipenv run ttlfmt dataset/ocsf.ttl

classes: categories events objects

# Add subClassOf based on subclass.extends -> superclass.name in schema (objects and events)
superclasses: classes
#	java -jar ../../bin/robot.jar -vvv query --input objects.ttl --update superclass-linking.ru --output objects-plus.ttl
	java -jar sparql-generate-2.1.0.jar -q superclasses.rqg -o dataset/ocsf.ttl --append-output
	pipenv run ttlfmt dataset/ocsf.ttl

# TODO continue to build up graph 
dictionary: classes
	java -jar sparql-generate-2.1.0.jar -q dictionary.rqg -o dataset/ocsf.ttl --append-output
	pipenv run ttlfmt dataset/ocsf.ttl

# Patched latest json-path-2.9.0.jar lib to handle enum matching
# Unpatched the baked-in json-path library doesn't handle some enum expressions, needs latest json-path (v2.9.0) lib and logic parallel to erestrictions
# This is temp hack to demonstrate TODO, but fetch lib here
# wget https://repo1.maven.org/maven2/com/jayway/jsonpath/json-path/2.9.0/json-path-2.9.0.jar
erestrictions: dictionary
	java -cp json-path-2.9.0.jar:sparql-generate-2.1.0.jar fr.mines_stetienne.ci.sparql_generate.cli.SPARQLExtCli -q erestrictions.rqg -o dataset/ocsf.ttl --append-output --base $(BASE_IRI)
# java -jar sparql-generate-2.1.0.jar -q erestrictions.rqg -o dataset/ocsf.ttl --append-output --base $(BASE_IRI)
	pipenv run ttlfmt dataset/ocsf.ttl

# TODO Complete
orestrictions: dictionary
	java -jar sparql-generate-2.1.0.jar -q orestrictions.rqg -o dataset/ocsf.ttl --append-output --base $(BASE_IRI)
	pipenv run ttlfmt dataset/ocsf.ttl

# Add all restrictions
restrictions: orestrictions erestrictions

# TODO Offline/Inop while working through restrictions
# equivalentClasses:
# 	java -jar sparql-generate-2.1.0.jar -q mappings.rqg -o mappings/d3fend-ocsf-mappings.ttl

# ocsf: base categories events objects superclasses dictionary restrictions equivalentClasses
ocsf: base categories events objects superclasses dictionary restrictions
	pipenv run ttlfmt dataset/ocsf.ttl

# # WILL HANDLE VIA OTHER PROPERTIES, OR EXTERNAL MAPPINGS
# # equivalentClasses:
# # 	java -jar sparql-generate-2.1.0.jar -q mappings.rqg -o mappings/d3fend-ocsf-mappings.ttl
# # 	pipenv run ttlfmt d3fend-ocsf-mappings.ttl

# Alternate method, may be out of date so check if switch over
# NOTE: ocsf.rqg is only needed for this alternate walk, but
# is a lot shorter than chained makefile here.
# ocsf-by-query: 
# 	java -jar sparql-generate-2.1.0.jar -q ocsf.rqg -o dataset/ocsf-by-query.ttl
# 	pipenv run ttlfmt dataset/ocsf-by-query.ttl

clean:
	find . -type f -name "*.ttl" -exec rm -f {} +

all: clean ocsf
	pipenv run ttlfmt dataset/ocsf.ttl
