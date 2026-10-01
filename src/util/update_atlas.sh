##
## This script creates a D3FEND ontology update from the ATLAS STIX JSON document
## Review build/atlas.updates.ttl against src/ontology/external/atlas.ttl.
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

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_atlas.py "$ATLAS_VERSION" || exit 1

pipenv run ttlfmt build/atlas.updates.ttl || exit 1

echo -e "${YELLOW}Created candidate module: build/atlas.updates.ttl \n"
echo -e "Review against src/ontology/external/atlas.ttl and replace that module when accepted. \n"
