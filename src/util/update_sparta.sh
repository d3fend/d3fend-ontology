##
## This script creates a D3FEND ontology update from SPARTA STIX
## Review build/sparta.updates.ttl against src/ontology/external/sparta.ttl.
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

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_sparta.py "$SPARTA_VERSION" || exit 1

pipenv run ttlfmt build/sparta.updates.ttl || exit 1

echo -e "${YELLOW}Created candidate module: build/sparta.updates.ttl \n"
echo -e "Review against src/ontology/external/sparta.ttl and replace that module when accepted. \n"
