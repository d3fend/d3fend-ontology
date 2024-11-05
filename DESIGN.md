# Design Details for the D3FEND Ontology

## IRI naming approach
The the ontology iri was selected to satisfy two key requirements:
1. The ontology prefix shall be a resolvable file.
2. A full IRI shall result in a resolvable file.

### Constraints
1. Must be compatible with standard static web file server


### Entity Deprecation Strategy
1. D3FEND uses the basic OWL2-DL deprecation strategy as generally implemented by Protege but with some additions, this involves:
   1. Setting an annotation property of `owl:deprecated` with a value of `true^^xsd:boolen`.
   1. Prepending the string `DEPRECATED ` to `rdfs:label` and any existing `rdfs:comment` .
   1. Adding a new `rdfs:comment` annotation explaining the deprecation rational and date.
   1. Deleting any existing `rdfs:seeAlso` annotations.
   1. Adding a new `rdfs:seeAlso` with an IRI value of new preferred class if applicable.
1. D3FEND will keep deprecated entities in the ontology for at least one year, afterwards they are subject to removal.
1. The D3FEND web application will render the deprecated entities for one year with a warning label.
