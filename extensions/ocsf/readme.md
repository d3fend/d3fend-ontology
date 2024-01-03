# ocsf

## Building
The extension is generated using SPARQL-Generate.

## Queries

### metaschema.rqg (optional)
The metaschema contains JSON Schema for each OCSF concept. This can be
used for validation, though at the moment it is just used for queries.

### dictionary.rqg
The attribute dictionary contains all available OCSF attributes.

This is the main source of properties to be mapped into D3FEND because
it declares attributes that are shared, and potentially overloaded, by
different events and objects. This should play well with a graph
model. The individual event and object classes can declare
restrictions on what properties are relevant to them.

If the attribute is a owl:DatatypeProperty then its rdfs:range should
be generated with the OCSF Datatype and when the class is known.

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

## Output (Goal)
Example outputs used to steer the generation toward useful RDF constructs.
### datatype

``` turtle
ocsf:port_t a rdfs:Datatype;
  rdfs:label           "Port";
  rdfs:subClassOf      xsd:integer;
  dcterms:description  "The TCP/UDP port number. For example: <code>80</code> or <code>22</code>.";
  xsd:maxInclusive     65535;
  xsd:minInclusive     0 .
```

### datatype property

``` turtle
ocsf:port a owl:DatatypeProperty;
  rdfs:label           "Port";
  rdfs:range           ocsf:port_t;
  dcterms:description  "The TCP/UDP port number associated with a connection. See specific usage." .
```

### object property

``` turtle

```
### todo
How to represent that an ocsf:attack can be related to a
d3f:OffensiveTactic, d3f:OffensiveTechnique, etc. The sub-techniques
are represented by subclasses of the top level offensive techniques
in D3FEND. So maybe the inference should be any d3f:ATTACKThing?
``` turtle
ocsf:attack rdfs:range d3f:ATTACKThing . 
```

``` turtle
# technique
?something ocsf:attack d3f:T1001 .
```

``` turtle
# subtechnique
?something ocsf:attack d3f:T1001.001 .
```

``` turtle
# tactic
?something ocsf:attack d3f:LateralMovement .
```
