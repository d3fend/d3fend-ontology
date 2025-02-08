# Install sparql-generate jar
install-sparql-generate:
	wget https://github.com/sparql-generate/sparql-generate/releases/download/2.1.0/sparql-generate-2.1.0.jar

# Put in the bin/jar directory
install-deps: install-sparql-generate

# Allows ability to quickly test SPARQL-Generate fragments
test:
	java -jar sparql-generate-2.1.0.jar -q test.rqg -o test.ttl
	pipenv run ttlfmt test.ttl
	more test.ttl

# The glue target covers any assertions that we choose to make directly
glue:
	java -jar sparql-generate-2.1.0.jar -q glue.rqg -o glue.ttl
	cp glue.ttl dataset/ocsf.ttl

categories: glue
	java -jar sparql-generate-2.1.0.jar -q categories.rqg -o categories.ttl
	cp glue.ttl dataset/ocsf.ttl
	cat categories.ttl | grep -v "^@prefix" >> dataset/ocsf.ttl

## Functional to here, events
events: categories
	java -jar sparql-generate-2.1.0.jar -q events.rqg -o events.ttl
	cp glue.ttl dataset/ocsf.ttl
	cat categories.ttl | grep -v "^@prefix" >> dataset/ocsf.ttl
	cat events.ttl | grep -v "^@prefix" >> dataset/ocsf.ttl

# TODO continue to build up graph 
objects: categories # No, no dependend on events
	java -jar sparql-generate-2.1.0.jar -q objects.rqg -o objects.ttl

# TODO continue to build up graph 
dictionary: events objects
	java -jar sparql-generate-2.1.0.jar -q dictionary.rqg -o dictionary.ttl

# TODO continue to build up graph 
restrictions: dictionary

# TODO continue to build up graph 
superclasses: event objects
	java -jar ../../bin/robot.jar -vvv query --input objects.ttl --update superclass-linking.ru --output objects-plus.ttl

# THIS WONT'T WORK AS SEQUENTIAL CALLS TO QUERIES DON'T ACCUMULATE IN THE GRAPH, ONLY BY LAUNDERING OUT TO THE GRAPH (here dataset.ocsf)
# ocsf: 
# 	java -jar sparql-generate-2.1.0.jar -q ocsf.rqg -o dataset/ocsf.ttl
# 	pipenv run ttlfmt dataset/ocsf.ttl

ocsf-hard: glue categories events objects dictionary restrictions superclasses
	pipenv run ttlfmt dataset/ocsf.ttl

# WILL HANDLE VIA OTHER PROPERTIES, OR EXTERNAL MAPPINGS
# equivalentClasses:
# 	java -jar sparql-generate-2.1.0.jar -q mappings.rqg -o mappings/d3fend-ocsf-mappings.ttl
# 	pipenv run ttlfmt d3fend-ocsf-mappings.ttl

clean:
	find . -type f -name "*.ttl" -exec rm -f {} +

all: ocsf equivalentClasses
