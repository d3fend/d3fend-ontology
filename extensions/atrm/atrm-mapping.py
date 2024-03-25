from io import StringIO
from pathlib import Path

from rdflib import DCTERMS as DC
from rdflib import OWL, RDFS, XSD, BNode, Graph, Literal, URIRef
from rdflib.extras.infixowl import Restriction
from ttlser.ttlfmt import convert

from tools import (
    ATRM,
    ATRMID,
    D3F,
    D3FEND,
    ATRMOffensiveTactic,
    ATRMOffensiveTechnique,
    a,
    atrm_base,
    atrm_data,
    get_external_refs,
    get_id,
    get_ref,
    get_techs_by_tactic,
    tactics,
    techniques,
    text,
    uri,
)

graph = Graph()

graph.bind("d3f", D3FEND)
graph.bind("atrm", ATRM)
graph.bind("dc", DC)
graph.bind("owl", OWL)


graph.add((URIRef(atrm_base), a, OWL.Ontology))
graph.add((D3F("description"), a, OWL.AnnotationProperty))
graph.add((D3F("enabled-by"), a, OWL.ObjectProperty))
graph.add((D3F("enables"), a, OWL.ObjectProperty))
graph.add((D3F("maps"), a, OWL.ObjectProperty))
graph.add((D3F("has-link"), a, OWL.DatatypeProperty))
graph.add((D3F("name"), a, OWL.DatatypeProperty))
graph.add((D3F("attack-kb-annotation"), a, OWL.AnnotationProperty))

graph.add((ATRMID, a, OWL.AnnotationProperty))
graph.add((ATRMID, RDFS.label, Literal("atrm-id")))
graph.add((ATRMID, RDFS.subPropertyOf, D3F("attack-kb-annotation")))
graph.add((ATRMID, RDFS.domain, ATRMOffensiveTechnique))
graph.add((ATRMID, RDFS.range, XSD.string))
graph.add(
    (
        ATRMID,
        D3F("definition"),
        Literal("x atrm-id y: The offensive technique x has the ATRM unique id of y."),
    )
)


ATRMThing = URIRef(ATRM + "ATRMThing")
graph.add((ATRMThing, a, OWL.Class))
graph.add((ATRMThing, RDFS.label, text("ATRM Thing")))
graph.add((ATRMThing, RDFS.subClassOf, D3F("Matrices")))


graph.add((ATRMOffensiveTactic, a, OWL.Class))
graph.add((ATRMOffensiveTactic, RDFS.subClassOf, D3F("OffensiveTactic")))
graph.add((ATRMOffensiveTactic, RDFS.label, text("ATRM Offensive Tactic")))

graph.add((ATRMOffensiveTechnique, a, OWL.Class))
graph.add((ATRMOffensiveTechnique, RDFS.subClassOf, ATRMThing))
graph.add((ATRMOffensiveTechnique, RDFS.subClassOf, D3F("OffensiveTechnique")))
graph.add((ATRMOffensiveTechnique, RDFS.label, text("ATRM Offensive Technique")))


for tactic in tactics:
    tactic_uri = URIRef(ATRM + tactic.x_mitre_shortname)
    graph.add((tactic_uri, RDFS.subClassOf, ATRMOffensiveTactic))
    graph.add((tactic_uri, a, OWL.Class))
    graph.add((tactic_uri, a, OWL.NamedIndividual))
    graph.add((tactic_uri, D3F("name"), text(tactic.name)))
    graph.add((tactic_uri, RDFS.label, text(f"ATRM {tactic.name} Tactic")))
    desc = tactic.description.replace('"', '\\"')
    graph.add((tactic_uri, DC.description, text(desc)))
    graph.add((tactic_uri, ATRMID, Literal(get_id(tactic))))
    graph.add((tactic_uri, D3F("maps"), D3F(tactic.name.replace(" ", ""))))

    # for tech in get_enabled_techs(atrm_data, tactic):
    #     graph.add((tactic_uri, D3F("enabled-by"), tech))
    #     graph.add((tactic_uri, D3F("enables"), tactic_uri))

    for ref in get_external_refs(tactic):
        graph.add((tactic_uri, RDFS.isDefinedBy, uri(ref)))

    tech_class = URIRef(ATRM + f'ATRM{tactic.name.replace(" ", "")}Technique')
    graph.add((tech_class, a, OWL.Class))
    graph.add((tech_class, RDFS.label, text(f"ATRM {tactic.name} Technique")))
    graph.add((tech_class, RDFS.subClassOf, URIRef(ATRM + "ATRMOffensiveTechnique")))

    r = BNode()
    Restriction(D3F("enables"), graph, someValuesFrom=tactic_uri, identifier=r)
    graph.add((tech_class, RDFS.subClassOf, r))

    for tech in get_techs_by_tactic(tactic):
        graph.add((URIRef(ATRM + get_id(tech)), RDFS.subClassOf, tech_class))

for technique in techniques:
    source = URIRef(ATRM + get_id(technique))
    graph.add((source, a, OWL.NamedIndividual))
    graph.add((source, D3F("name"), text(technique.name)))
    graph.add((source, RDFS.label, text(technique.name)))
    desc = technique.description.replace('"', '\\"')
    graph.add((source, DC.description, text(desc)))
    graph.add((source, ATRMID, Literal(get_id(technique))))
    graph.add((source, RDFS.isDefinedBy, get_ref(technique)))

    for ref in get_external_refs(technique):
        graph.add((source, D3F("has-link"), uri(ref)))

    for s in atrm_data.get_subtechniques_of_technique(technique.id):
        subtech = s["object"]
        subsource = URIRef(ATRM + get_id(subtech))
        graph.add((subsource, RDFS.subClassOf, source))
        graph.add((subsource, a, OWL.Class))
        graph.add((subsource, a, OWL.NamedIndividual))
        graph.add((subsource, D3F("name"), text(subtech.name)))
        graph.add((subsource, RDFS.label, text(subtech.name)))

        desc = subtech.description.replace('"', '\\"')
        graph.add((subsource, DC.description, text(desc)))
        graph.add((subsource, ATRMID, Literal(get_id(subtech))))
        graph.add((subsource, RDFS.isDefinedBy, get_ref(subtech)))

        for ref in get_external_refs(subtech):
            graph.add((subsource, D3F("has-link"), uri(ref)))


outpath = Path(__file__).parent / "build" / "atrm-ontology.ttl"
s = StringIO(graph.serialize())
convert(s, outpath=str(outpath), stream=True)
