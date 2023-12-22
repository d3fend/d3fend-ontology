# Install sparql-generate jar
install-sparql-generate:
	wget https://github.com/sparql-generate/sparql-generate/releases/download/2.1.0/sparql-generate-2.1.0.jar

# Put in the bin/jar directory
install-deps: install-sparql-generate

metaschema: 
	java -jar sparql-generate-2.1.0.jar -q metaschema.rqg -o metaschema.ttl

events: 
	java -jar sparql-generate-2.1.0.jar -q events.rqg -o events.ttl

objects: 
	java -jar sparql-generate-2.1.0.jar -q objects.rqg -o objects.ttl

dictionary: 
	java -jar sparql-generate-2.1.0.jar -q dictionary.rqg -o dictionary.ttl

clean:
	rm -Rf *ttl

all: metaschema
