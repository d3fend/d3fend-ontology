##
## This script creates a D3FEND ontology update from SPARTA STIX
## After running the user must manually compare & replace d3fend-protege.sparta.ttl
##

GREEN='\033[0;32m'
YELLOW='\033[0;33m'

SPARTA_VERSION=$1

sparta="data/sparta_data_v${SPARTA_VERSION}.json"
if [ ! -f "$sparta" ]; then
    echo -e "${GREEN}No SPARTA data found"
    echo -e "${GREEN}Running make download-sparta \n"
    make download-sparta SPARTA_VERSION="${SPARTA_VERSION}"
else
    echo -e "${GREEN}Using ${sparta} for SPARTA version ${SPARTA_VERSION} \n"
fi

cp src/ontology/d3fend-protege.ttl src/ontology/d3fend-protege.updates.ttl

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_sparta.py "$SPARTA_VERSION" || exit 1

pipenv run ttlfmt src/ontology/d3fend-protege.updates.ttl

echo -e "${YELLOW}Created new ontology file with updates here: src/ontology/d3fend-protege.updates.ttl \n"
echo -e "Please manually review and compare to: src/ontology/d3fend-protege.ttl \n"
echo -e "If changes acceptable, replace files \n"
