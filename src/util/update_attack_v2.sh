##
## This script creates a D3FEND ontology update from ATT&CK STIX JSON document
## for any missing ATT&CK techniques and puts them under the correct parent
## classes.
##

cp src/ontology/d3fend-protege.ttl src/ontology/d3fend-protege.updates.ttl

pipenv run python src/util/test_cases.py  || exit 1

pipenv run python src/util/update_attack_v2.py  || exit 1

pipenv run ttlfmt src/ontology/d3fend-protege.updates.ttl

echo Created new ontology file with updates here: src/ontology/d3fend-protege.updates.ttl
echo Please manually review and compare to: src/ontology/d3fend-protege.ttl
echo If changes acceptable, replace files 