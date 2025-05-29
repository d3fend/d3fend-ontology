##
## This script creates a D3FEND ontology update from the ATLAS STIX JSON document
## After running the user must manually compare & replace d3fend-protege.atlas.ttl
##

GREEN='\033[0;32m'
YELLOW='\033[0;33m'

ATLAS_VERSION=$1

atlas="data/stix-atlas.json"
if [ ! -f "$atlas" ]; then
    echo -e "${GREEN}No ATLAS file found \n"
    echo -e "${GREEN}Running make download-atlas ATLAS_VERSION=${ATLAS_VERSION} \n"
    make download-atlas ATLAS_VERSION="${ATLAS_VERSION}"
else
    echo -e "${GREEN}Using ${atlas} for atlas data \n"
fi

cp src/ontology/d3fend-protege.ttl src/ontology/d3fend-protege.atlas.ttl

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_atlas.py "$ATLAS_VERSION" || exit 1

pipenv run ttlfmt src/ontology/d3fend-protege.atlas.ttl

echo -e "${YELLOW}Created new ontology file with updates here: src/ontology/d3fend-protege.atlas.ttl \n"
echo -e "Please manually review and compare to: src/ontology/d3fend-protege.ttl \n"
echo -e "If changes acceptable, replace files \n"
