# ocsf

## Building
The extension is generated using SPARQL-Generate.

## Queries

### metaschema.rqg
The metaschema contains JSON Schema for each OCSF concept. This can be
used for validation, though at the moment it is just used for queries.

### dictionary.rqg
The attribute dictionary contains all available OCSF attributes and their
rdfs:range mapped to OWL classes and RDFS datatypes. 

### events.rqg
Events are declared subclasses of d3f:DigitalEvent that are related to
OCSF attributes. Restrictions are added for each related attribute.

### objects.rqg
Objects are collections of contextually related attributes in OCSF
that represent an entity. These object classes types should be mapped
to equivalent classes in D3FEND wherever appropriate. 

