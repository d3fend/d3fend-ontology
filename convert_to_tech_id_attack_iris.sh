#!/bin/sh
mkdir -p results/

bin/robot query --input d3fend-webprotege.owl \
    --query create_tech_id_attack_iri_mapping.rq results/attack-iri-rename.csv

bin/robot rename --input d3fend-webprotege.owl \
    --mappings results/attack-iri-rename.csv \
    --output results/d3fend-webprotege-attack-iri-rename.owl


