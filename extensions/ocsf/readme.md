# ocsf

Updated and aligned to 1.4.0 (but incomplete)
 
## Notes: 

To run Makefile and handle enumeration matching parts of
erestriction.rqg under development, you'll need this jar local:

wget https://repo1.maven.org/maven2/com/jayway/jsonpath/json-path/2.9.0/json-path-2.9.0.jar

Or get a version of sparql-generate-2.1.0.jar that actually has v2.9.0
of json-path bundled, which the one easily DL'd does not, it is at
v2.4.0.

## Building
The extension is generated using SPARQL-Generate.

## Queries (listed in order of execution)

### base.rqg
Handles base classes and top level alignments to D3FEND classes.

### categories.rqg
Handles category classes of OCSF for completeness. May not be essential.

### events.rqg
Events are declared subclasses of d3f:DigitalEvent that are related to
OCSF attributes. Restrictions are added later.

### event.rqg
This SPARQL-Generate function should take a source event in JSON
and construct an owl:Class definition for it.

### objects.rqg
Objects are collections of contextually related attributes in OCSF
that represent an entity. These object classes types should be mapped
to equivalent classes in D3FEND wherever appropriate. 

### object.rqg
This SPARQL-Generate function should take a source object in JSON and
construct an owl:Class definition for it. Restrictions are added
later.

### superclasses.rqg
Creates subClassOf assertions to tie clasases together

### dictionary.rqg
The attribute dictionary contains all available OCSF attributes.

This is the main source of properties to be mapped into D3FEND because
it declares attributes that are shared, and potentially overloaded, by
different events and objects. This should play well with a graph
model. The individual event and object classes can declare
restrictions on what properties are relevant to them.

If the attribute is a owl:DatatypeProperty then its rdfs:range should
be generated with the OCSF Datatype and when the class is known.

### erestrictions.rqg
With all the event classes in place creates restrictions based
on the related attributes as properties created by dictionary.rqg

### orestrictions.rqg
With all the object classes in place creates restrictions based
on the related attributes as properties created by dictionary.rqg

### type.rqg (currently offline)
This SPARQL-Generate function should take a source type in JSON
and construct an rdfs:Datatype definition for it.

### jsonschema.rqg (currently offline)
This SPARQL-Generate function should take a source object in JSON
Schema and construct a basic JSON Schema in RDF class representing it.

### mappings.rqg (offline)
Generates a relative handful of mappings annotated in OCSF; some are
semantic matches.

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

There have been significant changes to queries and Makefile to improve
the overall SPARQL-Generate and make it create an OWL 2 DL
representation of OCSF, this is still far from complete.  Current
sections only still reflect parts of steps.  For the passing moment
RTF Code (RTFC).

The queries for type.rqg and jsonschema.rqg will need to be
reintegrated.

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

## Bugs

* Fixed in this version by ordering of steps: 
  Generating multiples of the same restriction
  -- should this be filtered with another query?

``` turtle
rdfs:subClassOf      [ rdf:type            owl:Restriction;
                       owl:onProperty      ocsf:status_id;
                       owl:someValuesFrom  ocsf:integer_t
                     ];
rdfs:subClassOf      [ rdf:type            owl:Restriction;
                       owl:onProperty      ocsf:status_id;
                       owl:someValuesFrom  ocsf:integer_t
                     ];
```

