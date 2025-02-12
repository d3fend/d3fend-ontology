# Install sparql-generate jar
install-sparql-generate:
	wget https://github.com/sparql-generate/sparql-generate/releases/download/2.1.0/sparql-generate-2.1.0.jar

# Put in the bin/jar directory
install-deps: install-sparql-generate

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
	java -jar sparql-generate-2.1.0.jar -q events.rqg -o dataset/ocsf.ttl --append-output
	pipenv run ttlfmt dataset/ocsf.ttl

# TODO continue to build up graph 
objects: categories # Not dependent on events, AFAICT
	java -jar sparql-generate-2.1.0.jar -q objects.rqg -o dataset/ocsf.ttl --append-output
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

erestrictions: dictionary
	java -jar sparql-generate-2.1.0.jar -q erestrictions.rqg -o dataset/ocsf.ttl --append-output
	pipenv run ttlfmt dataset/ocsf.ttl

orestrictions: dictionary
	java -jar sparql-generate-2.1.0.jar -q orestrictions.rqg -o dataset/ocsf.ttl --append-output
	pipenv run ttlfmt dataset/ocsf.ttl

# Add all restrictions
restrictions: orestrictions erestrictions

ocsf: base categories events objects superclasses dictionary restrictions
# 	pipenv run ttlfmt dataset/ocsf.ttl

# # WILL HANDLE VIA OTHER PROPERTIES, OR EXTERNAL MAPPINGS
# # equivalentClasses:
# # 	java -jar sparql-generate-2.1.0.jar -q mappings.rqg -o mappings/d3fend-ocsf-mappings.ttl
# # 	pipenv run ttlfmt d3fend-ocsf-mappings.ttl

ocsf-by-query: 
	java -jar sparql-generate-2.1.0.jar -q ocsf.rqg -o dataset/ocsf-by-query.ttl
	pipenv run ttlfmt dataset/ocsf-by-query.ttl

clean:
	find . -type f -name "*.ttl" -exec rm -f {} +

all: clean ocsf
	pipenv run ttlfmt dataset/ocsf.ttl
