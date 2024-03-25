from io import StringIO
from pathlib import Path

from rdflib import DCTERMS as DC
from rdflib import OWL, RDF, RDFS, XSD, BNode, Graph, Literal, URIRef
from rdflib.extras.infixowl import Restriction
from ttlser.ttlfmt import convert

from tools import (
    D3F,
    D3FEND,
    TMFK,
    get_external_refs,
    get_id,
    get_ref,
    get_techs_by_tactic,
    tactics,
    techniques,
    text,
    tmfk_base,
    tmfk_data,
    uri,
)

TMFKOffensiveTactic = URIRef(TMFK + "TMFKOffensiveTactic")
TMFKOffensiveTechnique = URIRef(TMFK + "TMFKOffensiveTechnique")
TMFKMitigation = URIRef(TMFK + "TMFKMitigation")
TMFKID = URIRef(TMFK + "tmfk-id")

a = RDF.type

graph = Graph()

graph.bind("d3f", D3FEND)
graph.bind("tmfk", TMFK)
graph.bind("dc", DC)
graph.bind("owl", OWL)

graph.add((URIRef(tmfk_base), a, OWL.Ontology))
graph.add((D3F("description"), a, OWL.AnnotationProperty))
graph.add((D3F("enabled-by"), a, OWL.ObjectProperty))
graph.add((D3F("enables"), a, OWL.ObjectProperty))
graph.add((D3F("maps"), a, OWL.ObjectProperty))
graph.add((D3F("has-link"), a, OWL.DatatypeProperty))
graph.add((D3F("name"), a, OWL.DatatypeProperty))
graph.add((D3F("attack-kb-annotation"), a, OWL.AnnotationProperty))

graph.add((TMFKID, a, OWL.AnnotationProperty))
graph.add((TMFKID, RDFS.label, Literal("tmfk-id")))
graph.add((TMFKID, RDFS.subPropertyOf, D3F("attack-kb-annotation")))
graph.add((TMFKID, RDFS.domain, TMFKOffensiveTechnique))
graph.add((TMFKID, RDFS.range, XSD.string))
graph.add(
    (
        TMFKID,
        D3F("definition"),
        Literal("x tmfk-id y: The offensive technique x has the TMFK unique id of y."),
    )
)

TMFKThing = URIRef(TMFK + "TMFKThing")
graph.add((TMFKThing, a, OWL.Class))
graph.add((TMFKThing, RDFS.label, text("TMFK Thing")))
graph.add((TMFKThing, RDFS.subClassOf, D3F("Matrices")))

graph.add((TMFKOffensiveTactic, a, OWL.Class))
graph.add((TMFKOffensiveTactic, RDFS.subClassOf, D3F("OffensiveTactic")))
graph.add((TMFKOffensiveTactic, RDFS.label, text("TMFK Offensive Tactic")))

graph.add((TMFKOffensiveTechnique, a, OWL.Class))
graph.add((TMFKOffensiveTechnique, RDFS.subClassOf, TMFKThing))
graph.add((TMFKOffensiveTechnique, RDFS.subClassOf, D3F("OffensiveTechnique")))
graph.add((TMFKOffensiveTechnique, RDFS.label, text("TMFK Offensive Technique")))

graph.add((TMFKMitigation, a, OWL.Class))
graph.add((TMFKMitigation, RDFS.subClassOf, TMFKThing))
graph.add((TMFKMitigation, RDFS.subClassOf, D3F("Mitigation")))
graph.add((TMFKMitigation, RDFS.label, text("TMFK Mitigation")))

for tactic in tactics:
    tactic_uri = URIRef(TMFK + tactic.x_mitre_shortname)
    graph.add((tactic_uri, RDFS.subClassOf, TMFKOffensiveTactic))
    graph.add((tactic_uri, a, OWL.Class))
    graph.add((tactic_uri, a, OWL.NamedIndividual))
    graph.add((tactic_uri, D3F("name"), text(tactic.name)))
    graph.add((tactic_uri, RDFS.label, text(f"TMFK {tactic.name} Tactic")))
    desc = tactic.description.replace('"', '\\"')
    graph.add((tactic_uri, DC.description, text(desc)))
    graph.add((tactic_uri, TMFKID, Literal(get_id(tactic))))
    graph.add((tactic_uri, D3F("maps"), D3F(tactic.name.replace(" ", ""))))

    # for tech in get_enabled_techs(tmfk_data, tactic):
    #     graph.add((tactic_uri, D3F("enabled-by"), tech))
    #     graph.add((tech, D3F("enables"), tactic_uri))

    for ref in get_external_refs(tactic):
        graph.add((tactic_uri, RDFS.isDefinedBy, uri(ref)))

    tech_class = URIRef(TMFK + f'TMFK{tactic.name.replace(" ", "")}Technique')
    graph.add((tech_class, a, OWL.Class))
    graph.add((tech_class, RDFS.label, text(f"TMFK {tactic.name} Technique")))
    graph.add((tech_class, RDFS.subClassOf, URIRef(TMFK + "TMFKOffensiveTechnique")))

    r = BNode()
    Restriction(D3F("enables"), graph, someValuesFrom=tactic_uri, identifier=r)
    graph.add((tech_class, RDFS.subClassOf, r))

    for tech in get_techs_by_tactic(tactic):
        graph.add((URIRef(TMFK + get_id(tech)), RDFS.subClassOf, tech_class))

for technique in techniques:
    source = URIRef(TMFK + get_id(technique))
    graph.add((source, a, OWL.Class))
    graph.add((source, a, OWL.NamedIndividual))
    graph.add((source, D3F("name"), text(technique.name)))
    graph.add((source, RDFS.label, text(technique.name)))
    desc = technique.description.replace('"', '\\"')
    graph.add((source, DC.description, text(desc)))
    graph.add((source, TMFKID, Literal(get_id(technique))))
    graph.add((source, RDFS.isDefinedBy, get_ref(technique)))

    for ref in get_external_refs(technique):
        graph.add((source, D3F("has-link"), uri(ref)))

    for m in tmfk_data.get_mitigations_mitigating_technique(technique.id):
        mitigation = m["object"]
        mitigation_source = URIRef(TMFK + get_id(mitigation))

        # graph.add((mitigation_source, RDFS.subClassOf, source))
        graph.add((mitigation_source, a, TMFKMitigation))
        graph.add((mitigation_source, D3F("name"), text(mitigation.name)))
        graph.add((mitigation_source, RDFS.label, text(mitigation.name)))
        desc = mitigation.description.replace('"', '\\"')
        graph.add((mitigation_source, DC.description, text(desc)))
        graph.add((mitigation_source, TMFKID, Literal(get_id(mitigation))))
        graph.add((mitigation_source, RDFS.isDefinedBy, get_ref(mitigation)))

        if "x_mitre_ids" in mitigation._inner:
            for mitre_mitig in mitigation.x_mitre_ids:
                graph.add((mitigation_source, D3F("maps"), D3F(mitre_mitig)))

        graph.add(
            (mitigation_source, D3F("mitigates"), URIRef(TMFK + get_id(technique)))
        )

        for ref in get_external_refs(mitigation):
            graph.add((mitigation_source, D3F("has-link"), uri(ref)))

    for s in tmfk_data.get_subtechniques_of_technique(technique.id):
        subtech = s["object"]
        subsource = URIRef(TMFK + get_id(subtech))
        graph.add((subsource, RDFS.subClassOf, source))
        graph.add((subsource, RDFS.subClassOf, TMFKOffensiveTechnique))
        graph.add((subsource, a, OWL.Class))
        graph.add((subsource, a, OWL.NamedIndividual))
        graph.add((subsource, D3F("name"), text(subtech.name)))
        graph.add((subsource, RDFS.label, text(subtech.name)))

        desc = subtech.description.replace('"', '\\"')
        graph.add((subsource, DC.description, text(desc)))
        graph.add((subsource, TMFKID, Literal(get_id(subtech))))
        graph.add((subsource, RDFS.isDefinedBy, get_ref(subtech)))

        for ref in get_external_refs(subtech):
            graph.add((subsource, D3F("has-link"), uri(ref)))

        for m in tmfk_data.get_mitigations_mitigating_technique(subtech.id):
            mitigation = m["object"]
            mitigation_source = URIRef(TMFK + get_id(mitigation))

            graph.add((mitigation_source, a, TMFKMitigation))
            graph.add((mitigation_source, D3F("name"), text(mitigation.name)))
            graph.add((mitigation_source, RDFS.label, text(mitigation.name)))
            desc = mitigation.description.replace('"', '\\"')
            graph.add((mitigation_source, DC.description, text(desc)))
            graph.add((mitigation_source, TMFKID, Literal(get_id(mitigation))))
            graph.add((mitigation_source, RDFS.isDefinedBy, get_ref(mitigation)))

            if "x_mitre_ids" in mitigation._inner:
                for mitre_mitig in mitigation.x_mitre_ids:
                    graph.add((mitigation_source, D3F("maps"), D3F(mitre_mitig)))

            graph.add(
                (mitigation_source, D3F("mitigates"), URIRef(TMFK + get_id(subtech)))
            )

            for ref in get_external_refs(mitigation):
                graph.add((mitigation_source, D3F("has-link"), uri(ref)))

outpath = Path(__file__).parent / "build" / "tmfk-ontology.ttl"
s = StringIO(graph.serialize())
convert(s, outpath=str(outpath), stream=True)
