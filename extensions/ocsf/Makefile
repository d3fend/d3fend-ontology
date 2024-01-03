# Install sparql-generate jar
install-sparql-generate:
	wget https://github.com/sparql-generate/sparql-generate/releases/download/2.1.0/sparql-generate-2.1.0.jar

# Put in the bin/jar directory
install-deps: install-sparql-generate

events: 
	java -jar sparql-generate-2.1.0.jar -q events.rqg -o events.ttl

objects: 
	java -jar sparql-generate-2.1.0.jar -q objects.rqg -o objects.ttl

dictionary: 
	java -jar sparql-generate-2.1.0.jar -q dictionary.rqg -o dictionary.ttl

ocsf: 
	java -jar sparql-generate-2.1.0.jar -q ocsf.rqg -o dataset/ocsf.ttl

equivalentClasses: 
	java -jar sparql-generate-2.1.0.jar -q mappings.rqg -o mappings/d3fend-ocsf-mappings.ttl

clean:
	rm -Rf *ttl

all: ocsf equivalentClasses
