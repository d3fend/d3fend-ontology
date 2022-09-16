##
## This script creates a D3FEND ontology mapping from an Excel
## spreadsheet containing NIST control to D3FEND mappings and inserts
## them into the d3fend ontology.  Updates to the sheet would require
## re-running.
##
## After inspection, promote the d3fend_protege.nist.ttl file to d3fend_protege

echo creating d3fend-protege.owl for owlready2...
bin/robot convert --input src/ontology/d3fend-protege.ttl --output d3fend-protege.owl

echo creating NIST mappings in ttl...
pipenv run python extensions/nist/create_nist_mappings.py || exit 1

echo concatenating ttl for merge of controls with ontology...
cat src/ontology/d3fend-protege.ttl > src/ontology/d3fend-protege.nist.ttl
cat sp800-53r5-control-to-d3fend-mapping.ttl >> src/ontology/d3fend-protege.nist.ttl

echo reformatting ttl...
pipenv run ttlfmt src/ontology/d3fend-protege.nist.ttl

echo Created new ontology with NIST control mappings with updates here: src/ontology/d3fend-protege.nist.ttl

function cleanup(){
    echo -e "\t deleting: $1"
    rm -f $1
}

echo cleaning up:
cleanup d3fend-protege.owl # was JIT creation at start for owlready use.
cleanup sp800-53r5-control-to-d3fend-mapping.ttl # now merged
