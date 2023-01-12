#!/bin/sh
#
# Helps sift out deltas from a past baseline version so the deltas can patched into some other branch/fork.
# 
# 1. Run (it will run in build/ directory context)
#
# 2. Review build/d3fend-merged.ttl result and move from build to save
#    or delete; it might be the next commit for the file
#    src/ontology/defend-protege.ttl.
#
# Example invocation:
# ./patch-ontology.sh ~/Downloads/d3fend-protege-jun29.ttl ~/Downloads/d3fend-protege-lbs-v5.ttl ~/Downloads/d3fend-protege-66.ttl

# Baseline (the baseline from which the patch will be based), Mod (delta from Baseline to this), Target baseline (patch this baseline with the identified diffs)
baseline=$1 # e.g., ../d3fend-protege-jun29.ttl              (d3fend-protege.ttl basaeline as of 29 jun, which was version linda would've been working; that is, notionally "feature-branching" from)
mod=$2      # e.g., ~/Downloads/d3fend-protege-lbs-v5.ttl (linda's edited protege file)
target=$3   # e.g., ~/Downloads/d3fend-protege-66.ttl     (branch chosen to merge into; PK's CWE branch)

# Find diffs and the axioms to delete and remove
# Left is baseline to patch; right is desired patch end-state;
cd ../build
java -jar ../bin/robot.jar diff --left $baseline --right $mod --output diff.txt # OWL functional syntax axioms with +/- prefix indicators for add/remove to patch
grep "^- " diff.txt | cut -c 3- > deletes.ofna                                  # separate out the axioms to remove to one file (.ofna not .ofn --- as not matching syntax for overall file)
grep "^+ " diff.txt | cut -c 3- > inserts.ofna                                  # separate out the axioms to add to one filre   (.ofna not .ofn)

# OWL Function Syntax for namespace prefixes and to open/"begin" Ontology specification
d3fend_ofn_prefix="Prefix(:=<http://d3fend.mitre.org/ontologies/d3fend.owl#>)\n\
Prefix(owl:=<http://www.w3.org/2002/07/owl#>)\n\
Prefix(rdf:=<http://www.w3.org/1999/02/22-rdf-syntax-ns#>)\n\
Prefix(xml:=<http://www.w3.org/XML/1998/namespace>)\n\
Prefix(xsd:=<http://www.w3.org/2001/XMLSchema#>)\n\
Prefix(rdfs:=<http://www.w3.org/2000/01/rdf-schema#>)\n\
Prefix(skos:=<http://www.w3.org/2004/02/skos/core#>)\n\
Prefix(dcterms:=<http://purl.org/dc/terms/>)\n\
\n\
Ontology(<http://d3fend.mitre.org/ontologies/d3fend.owl>\n\
"

# close/"end" ontology
d3fend_ofn_suffix="\n\
)"

# Put necessary wrapper/sugar around axioms so the OWL functional syntax [aka notation; hence .ofn suffix] works as complete ontology file readable by OWL API
echo $d3fend_ofn_prefix  >  unmerge.ofn
cat deletes.ofna         >> unmerge.ofn
echo $d3fend_ofn_suffix  >> unmerge.ofn

echo $d3fend_ofn_prefix >  merge.ofn
cat inserts.ofna        >> merge.ofn
echo $d3fend_ofn_suffix >> merge.ofn

# bin/robot convert --input merge.ofn --output merge.ttl # Bonus version in ttl if preferred for check over ofn.

# Do unmerge, then merge against the ontology we are adding patch to.
java -jar ../bin/robot.jar unmerge --input $target             --input unmerge.ofn --output d3fend-unmerged.ttl # Order matters removals only in first --input.
java -jar ../bin/robot.jar merge   --input d3fend-unmerged.ttl --input merge.ofn   --output d3fend-merged.ttl

# Review d3fend-merged.ttl, replace d3fend-protege.owl with it, and merge that change into feature branch

# Cleanup intermediate build/ files, 
rm deletes.ofna inserts.ofna unmerge.ofn merge.ofn d3fend-unmerged.ttl diff.txt

