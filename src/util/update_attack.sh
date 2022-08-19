##
## This script creates a D3FEND ontology update from ATT&CK STIX JSON document
## for any missing ATT&CK techniques and puts them under the correct parent
## classes.
##
## After running this script, the developer needs to manually add:
##  - Attack Tactics and relate them to the "Tactic-Technique" classes.
##  - Remove any deprecated techniques as necessary.
##

pipenv run python src/util/update_attack.py || exit 1

./bin/robot template \
    --template reports/attack_update-missing_attack_ids-robot_template.csv \
    --ontology-iri http://d3fend.mitre.org/ontologies/d3fend.owl \
    --prefix "d3f: http://d3fend.mitre.org/ontologies/d3fend.owl#" \
    -o src/ontology/_attack_update.ttl

# remove robot's uncessary type annotation
# works on both bsd and gnu sed
sed -e "s/\^\^xsd\:string//g" src/ontology/_attack_update.ttl > src/ontology/attack_update.ttl

./bin/robot merge \
    --add-prefix "dcterms: http://purl.org/dc/terms/" \
    --add-prefix "skos: http://www.w3.org/2004/02/skos/core#" \
    -i src/ontology/d3fend-protege.ttl \
    -i src/ontology/attack_update.ttl \
    -o src/ontology/d3fend-protege.attack_update.ttl \

pipenv run ttlfmt src/ontology/d3fend-protege.attack_update.ttl

echo Created new ontology file with updates here: src/ontology/d3fend-protege.attack_update.ttl
echo Please manually review and compare to: src/ontology/d3fend-protege.ttl


function cleanup(){
    echo -e "\t deleting: $1"
    rm -f $1
}

echo cleaning up:
cleanup src/ontology/_attack_update.ttl
cleanup src/ontology/attack_update.ttl
