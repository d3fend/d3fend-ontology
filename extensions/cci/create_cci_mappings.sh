##
## This script creates a D3FEND ontology mapping from an Excel
## spreadsheet containing NIST control to D3FEND mappings and inserts
## them into the d3fend ontology.  Updates to the sheet would require
## re-running.
##
## CAUTION: This will overwrite the prior d3fend-protege.ttl file with
## the mappings merged.  Roll back with git if you encounter problems
## loading the merged ontology.
##

pipenv run python extensions/cci/create_cci_mappings.py || exit 1

./bin/robot merge \
    --add-prefix "dcterms: http://purl.org/dc/terms/" \
    --add-prefix "skos: http://www.w3.org/2004/02/skos/core#" \
    -i src/ontology/d3fend-protege.ttl \
    -i extensions/cci/cci-to-d3fend-mapping.ttl \
    -o src/ontology/d3fend-protege.ttl \

pipenv run ttlfmt src/ontology/d3fend-protege.ttl

echo Overwrote ontology file with updates on: src/ontology/d3fend-protege.ttl
echo CAUTION: If you encounter problems, rollback with git

function cleanup(){
    echo -e "\t deleting: $1"
    rm -f $1
}

echo cleaning up:
cleanup extensions/cci/cci-to-d3fend-mapping.ttl
