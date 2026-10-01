##
## This script creates a D3FEND ontology update from CAPEC XML
## Review build/capec.updates.ttl against src/ontology/external/capec.ttl.
##

GREEN='\033[0;32m'
YELLOW='\033[0;33m'

CAPEC_VERSION=$1

capec="data/capec_v${CAPEC_VERSION}.xml"
if [ ! -f "$capec" ]; then
    echo -e "${GREEN}No CAPEC list found"
    echo -e "${GREEN}Running make download-capec \n"
    make download-capec CAPEC_VERSION="${CAPEC_VERSION}"
else
    echo -e "${GREEN}Using ${capec} for CAPEC version ${CAPEC_VERSION} \n"
fi

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_capec.py "$CAPEC_VERSION" || exit 1

pipenv run ttlfmt build/capec.updates.ttl || exit 1

echo -e "${YELLOW}Created candidate module: build/capec.updates.ttl \n"
echo -e "Review against src/ontology/external/capec.ttl and replace that module when accepted. \n"
