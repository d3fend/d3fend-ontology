PREFIX ocsf: <https://schema.ocsf.io/1.3.0/ontology/>
PREFIX d3f: <http://d3fend.mitre.org/ontologies/d3fend.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX jsonschema: <https://www.w3.org/2019/wot/json-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX iter: <http://w3id.org/sparql-generate/iter/>
PREFIX fun: <http://w3id.org/sparql-generate/fn/>

INSERT {
  ?class rdfs:subClassOf ?superClass .
}
WHERE {
  ?class a owl:Class ;
     ocsf:extends ?name .
  ?superClass a owl:Class ;
     ocsf:name ?name .
}
