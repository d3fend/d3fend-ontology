# Install yarrrml-parser
CWE_URL ?= https://cwe.mitre.org/data/xml/cwec_latest.xml.zip

install-yarrrml-parser:
	npm install

# Install yarrml-mapper jar
install-yarrrml-mapper:
	wget https://github.com/RMLio/rmlmapper-java/releases/download/v7.3.3/rmlmapper-7.3.3-r374-all.jar

# Put in the bin/jar directory
install-deps: install-yarrrml-parser install-yarrrml-mapper

# Pull CWE file; unzip; convert versioned into stable target 'cwec.xml' for YARRRML (and RML) specification
download-cwe:
	curl -L $(CWE_URL) -o cwec_latest.xml.zip
	unzip -o cwec_latest.xml.zip
	rm cwec_latest.xml.zip
	mv -f "$$(find . -type f -name 'cwec_v*.xml')" "cwec_latest.xml"

# Run parser on YARRRML file
parse-yarrrml: cwe-yarrrml.yaml
	node_modules/.bin/yarrrml-parser -i cwe-yarrrml.yaml -o cwe-rules.rml.ttl

# Generate CWE triples; rmlmapper writes N-Triples for the subsequent merge.
create-cwe-triples: download-cwe parse-yarrrml
	java -jar rmlmapper-7.3.3-r374-all.jar -m cwe-rules.rml.ttl --output cwe-all-out.nt

# Merge only the CWE module's asserted axioms into a reviewable candidate.
# Use --add-prefix to prevent replacement of dcterms/skos prefixes with ns1, ns2 during robot's merge
merge-cwe-with-d3fend: create-cwe-triples
	mkdir -p ../../build
	java -jar ../../bin/robot.jar merge --catalog ../../src/ontology/catalog-v001.xml --collapse-import-closure false --include-annotations true --input ../../src/ontology/external/cwe.ttl --input cwe-all-out.nt --output ../../build/cwe.updates.ttl --add-prefix "dcterms: http://purl.org/dc/terms/" --add-prefix "skos: http://www.w3.org/2004/02/skos/core#"
	cd ../.. && pipenv run ttlfmt build/cwe.updates.ttl
	@echo "Review build/cwe.updates.ttl against src/ontology/external/cwe.ttl before replacing that module."
	@echo "Remove redundant subClassOf :Weakness assertions on non-pillar classes when the imported hierarchy supplies intermediate classes."

clean:
	rm -Rf *ttl *nt

all: merge-cwe-with-d3fend
