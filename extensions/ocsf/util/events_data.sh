#!/bin/bash
# Run in the top level directory of ocsf-schema repo clone
# grep -r extends ./* | grep events  | grep -v extensions | grep -v events_matcher | grep -v profiles > events_data.txt
# or this hard-coded version works
WRITE_DIR=$(pwd)
cd  ~/github/ocsf-schema ; grep -r extends ./*  | grep events | grep -v extensions | grep -v events_matcher | grep -v profiles > ${WRITE_DIR}/events_data.txt
