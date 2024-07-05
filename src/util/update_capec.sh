##
## This script creates a D3FEND ontology update from CAPEC XML
## After running the user must manually compare & replace d3fend-protege.capec.ttl
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

cp src/ontology/d3fend-protege.ttl src/ontology/d3fend-protege.capec.ttl

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_capec.py "$CAPEC_VERSION" || exit 1

pipenv run ttlfmt src/ontology/d3fend-protege.capec.ttl

echo -e "${YELLOW}Created new ontology file with updates here: src/ontology/d3fend-protege.capec.ttl \n"
echo -e "Please manually review and compare to: src/ontology/d3fend-protege.ttl \n"
echo -e "If changes acceptable, replace files \n"
