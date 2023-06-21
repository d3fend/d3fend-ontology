# Install yarrrml-parser
install-yarrrml-parser:
	npm install

# Install yarrml-mapper jar
install-yarrrml-mapper:
	wget https://github.com/RMLio/rmlmapper-java/releases/download/v6.1.3/rmlmapper-6.1.3-r367-all.jar

# Put in the bin/jar directory
install-deps: install-yarrrml-parser install-yarrrml-mapper

# Pull CWE file; unzip; convert versioned into stable target 'cwec.xml' for YARRRML (and RML) specification
download-cwe:
	curl https://cwe.mitre.org/data/xml/cwec_latest.xml.zip -o cwec_latest.xml.zip
	unzip cwec_latest.xml.zip
	rm cwec_latest.xml.zip
	mv -f "$$(find . -type f -name 'cwec_v*.xml')" "cwec_latest.xml"

# Run parser on YARRRML file
parse-yarrrml: cwe-yarrrml.yaml
	node_modules/.bin/yarrrml-parser -i cwe-yarrrml.yaml -o cwe-rules.rml.ttl

# Run mapper on d3fend-protege.ttl; as of 2023-06-19, rmlmapper doesn't have .ttl as serializationformat.
create-cwe-triples: download-cwe parse-yarrrml
	java -jar rmlmapper-6.1.3-r367-all.jar -m cwe-rules.rml.ttl --output cwe-all-out.nt

# Run robot to merge to defend-protege.ttl (assume ROBOT in place in bin; test)
# Use --add-prefix to prevent replacement of dcterms/skos prefixes with ns1, ns2 during robot's merge
merge-cwe-with-d3fend: create-cwe-triples
	java -jar ../../bin/robot.jar merge --include-annotations true --input ../../src/ontology/d3fend-protege.ttl --input cwe-all-out.nt --output ../../src/ontology/d3fend-protege.ttl --add-prefix "dcterms: http://purl.org/dc/terms/" --add-prefix "skos: http://www.w3.org/2004/02/skos/core#"
	cd ../..; make format
	@echo "Now use Protege to manually remove the subClassOf :Weakness statements that were on Top 25 classes and aren't pillars, as they are not direct subclasses of :Weakness.  Hint: Reference git diff on d3fend-protege.tll and search for - on :Weakness."

clean:
	rm -Rf *ttl *nt

all: merge-cwe-with-d3fend
