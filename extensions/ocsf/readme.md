# ocsf

## Building
The extension is generated using SPARQL-Generate.

## Queries

### metaschema.rqg (optional)
The metaschema contains JSON Schema for each OCSF concept. This can be
used for validation, though at the moment it is just used for queries.

### dictionary.rqg
The attribute dictionary contains all available OCSF attributes and their
rdfs:range mapped to OWL classes and RDFS datatypes. 

This is the main source of properties to be mapped into D3FEND because
it declares attributes that are shared, and potentially overloaded, by
different events and objects. This should play well with a graph
model. The individual event and object classes can declare
restrictions on what properties are relevant to them.

### events.rqg
Events are declared subclasses of d3f:DigitalEvent that are related to
OCSF attributes. Restrictions are added for each related attribute.

### objects.rqg
Objects are collections of contextually related attributes in OCSF
that represent an entity. These object classes types should be mapped
to equivalent classes in D3FEND wherever appropriate. 

### attribute.rqg
This SPARQL-Generate function should take a source attribute in JSON
and construct an owl:DatatypeProperty or owl:ObjectProperty based on
the known constraints declared in OCSF via the attribute dictionary.

### type.rqg
This SPARQL-Generate function should take a source type in JSON
and construct an rdfs:Datatype definition for it.

### event.rqg
This SPARQL-Generate function should take a source event in JSON
and construct an owl:Class definition for it with restrictions based
on the related attributes.

### object.rqg
This SPARQL-Generate function should take a source object in JSON
and construct an owl:Class definition for it with restrictions based
on the related attributes.

### jsonschema.rqg
This SPARQL-Generate function should take a source object in JSON
Schema and construct a basic JSON Schema in RDF class representing it.



