##
## This script creates a D3FEND ontology update from ATT&CK STIX JSON document
## After running the user must manually compare & replace d3fend-protege.updates.ttl
##

GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

ATTACK_VERSION=$1
shift

if [ "$#" -gt 0 ]; then
    FRAMEWORKS=("$@")
else
    FRAMEWORKS=("enterprise" "ics" "mobile")
fi

for framework in "${FRAMEWORKS[@]}"; do
    case "$framework" in
        enterprise|ics|mobile)
            ;;
        *)
            echo -e "${RED}Unsupported framework '${framework}'. Supported values: enterprise, ics, mobile.${RESET}"
            exit 1
            ;;
    esac
done

missing_data=false
for framework in "${FRAMEWORKS[@]}"; do
    stix_path="data/${framework}-attack-${ATTACK_VERSION}.json"
    if [ ! -f "$stix_path" ]; then
        missing_data=true
        break
    fi
done

if [ "$missing_data" = true ]; then
    echo -e "${GREEN}One or more ATT&CK data files are missing."
    echo -e "${GREEN}Running make download-attack \n"
    make download-attack ATTACK_VERSION="${ATTACK_VERSION}"
fi

for framework in "${FRAMEWORKS[@]}"; do
    stix_path="data/${framework}-attack-${ATTACK_VERSION}.json"
    if [ -f "$stix_path" ]; then
        echo -e "${GREEN}Using ${stix_path} for ${framework} attack data \n"
    else
        echo -e "${RED}Expected file ${stix_path} was not downloaded successfully.${RESET}"
        exit 1
    fi
done

cp src/ontology/d3fend-protege.ttl src/ontology/d3fend-protege.updates.ttl

pipenv run python src/util/test_cases.py  || exit 1

echo -e "${GREEN}All test cases passed \n"

pipenv run python src/util/update_attack.py "$ATTACK_VERSION" "${FRAMEWORKS[@]}" || exit 1

pipenv run ttlfmt src/ontology/d3fend-protege.updates.ttl

echo -e "${YELLOW}Created new ontology file with updates here: src/ontology/d3fend-protege.updates.ttl \n"
echo -e "Please manually review and compare to: src/ontology/d3fend-protege.ttl \n"
echo -e "If changes acceptable, replace files \n"
