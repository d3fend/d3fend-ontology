##
## This script creates a D3FEND ontology update from ATT&CK STIX JSON document
## After running the user must manually compare & replace d3fend-protege.updates.ttl
##

ATTACK_VERSION="13.1" # Current Attack Version 

GREEN='\033[0;32m'
YELLOW='\033[0;33m'

enterprise_attack="data/enterprise-attack-${ATTACK_VERSION}.json"
if [ ! -f "$enterprise_attack" ]; then
    echo -e "${GREEN}No enterprise attack file found"
    echo -e "${GREEN}Running make download-attack \n"
    make download-attack ATTACK_VERSION="${ATTACK_VERSION}"
else 
    echo -e "${GREEN}Using ${enterprise_attack} for attack data \n"
fi

cp src/ontology/d3fend-protege.ttl src/ontology/d3fend-protege.updates.ttl

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_attack.py "$ATTACK_VERSION" || exit 1

pipenv run ttlfmt src/ontology/d3fend-protege.updates.ttl

echo -e "${YELLOW}Created new ontology file with updates here: src/ontology/d3fend-protege.updates.ttl \n"
echo -e "Please manually review and compare to: src/ontology/d3fend-protege.ttl \n"
echo -e "If changes acceptable, replace files \n"