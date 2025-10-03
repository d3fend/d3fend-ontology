# Design Details for the D3FEND Ontology

## Definitions
1. Definitions (d3f:definition) should be [well](https://www.nist.gov/system/files/documents/2021/10/14/nist-ai-rfi-cubrc_inc_002.pdf) formed and concise.
2. If you find yourself writing the work "or" many times, reconsider your taxonomy.

## IRI naming approach
The the ontology iri was selected to satisfy two key requirements:
1. The ontology prefix shall be a resolvable file.
2. A full IRI shall result in a resolvable file.

### Constraints
1. Must be compatible with standard static web file server

### Restrictions
1. Model contains (part-of or has-component) relationships from the parent only. The contained-by relationship will be left to the reasoner.
