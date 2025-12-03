from stix2 import MemoryStore, Filter
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

import sys

D3F = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


def get_sparta_id(tech):
    """
    Get the SPARTA ID from a STIX Technique object
    :param tech: STIX Technique object
    :return: SPARTA ID or None
    """
    return next(
        (
            ref.get("external_id")
            for ref in tech["external_references"]
            if ref.get("source_name") == "sparta"
            and not ref.get("external_id").startswith("D3")
        ),
        None,
    )


def add_technique_to_graph(src, g, tech):
    """
    Add a SPARTA Technique to the graph
    :param src: MemoryStore
    :param g: Graph
    :param tech: STIX attack-pattern object that is a SPARTA Technique
    """
    sparta_id = get_sparta_id(tech)
    # If the technique has a SPARTA ID, add it to the graph
    if sparta_id is not None:
        # Create a URI for the SPARTA Technique
        sparta_uri = D3F[f"{sparta_id}"]
        g.add((sparta_uri, RDF.type, OWL.Class))
        g.add((sparta_uri, RDFS.label, Literal(tech["name"].strip() + " - SPARTA")))
        g.add((sparta_uri, SKOS.prefLabel, Literal(tech["name"].strip())))
        sparta_url = next(
            (
                ref.get("url")
                for ref in tech["external_references"]
                if ref.get("source_name") == "sparta"
            ),
            None,
        )
        g.add((sparta_uri, RDFS.seeAlso, URIRef(sparta_url)))
        g.add((sparta_uri, D3F.definition, Literal(tech["description"])))
        g.add((sparta_uri, D3F["attack-id"], Literal(sparta_id)))
        # NOTE: as of v1.6, SPARTA STIX data has "x_sparta_is_subtechnique" set to False for everything, so this is a workaround
        # If the SPARTA ID has a period, it is a sub-technique
        if "." in sparta_id:
            g.add((sparta_uri, RDFS.subClassOf, D3F[f"{sparta_id.split('.')[0]}"]))
        else:
            # Interpret the kill chain phase name as the parent technique classified by tactic
            for obj in tech.get("kill_chain_phases", []):
                name = str("SPARTA" + obj["phase_name"] + " Technique").replace(" ", "")
                g.add((sparta_uri, RDFS.subClassOf, D3F[name]))


def get_sparta_graph(sparta_path, d3fend_graph):
    """
    Get a graph of SPARTA Techniques
    :param sparta_path: Path to SPARTA JSON data
    :param d3fend_graph: Graph of D3FEND Ontology
    :return: Graph of SPARTA Techniques
    """
    src = MemoryStore()
    src.load_from_file(sparta_path)

    techniques = src.query(
        [
            Filter("type", "=", "attack-pattern"),
            Filter("external_references.source_name", "=", "sparta"),
            Filter(
                "external_references.url",
                "contains",
                "https://sparta.aerospace.org/technique/",
            ),
            Filter("kill_chain_phases.kill_chain_name", "=", "sparta"),
        ]
    )

    # Create a new graph
    g = Graph()

    # Add SPARTA Techniques to the graph
    for tech in techniques:
        add_technique_to_graph(src, g, tech)

    return g


def main(SPARTA_VERSION="3.1"):

    d3fend_graph = Graph()
    d3fend_graph.parse("src/ontology/d3fend-protege.updates.ttl")

    sparta_graph = get_sparta_graph(
        f"data/sparta_data_v{SPARTA_VERSION}.json", d3fend_graph
    )

    d3fend_graph += sparta_graph

    d3fend_graph.serialize(
        destination="src/ontology/d3fend-protege.updates.ttl", format="turtle"
    )


if __name__ == "__main__":
    version = sys.argv[1]
    main(SPARTA_VERSION=version)
