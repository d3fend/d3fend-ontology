from stix2 import MemoryStore, Filter
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

from html.parser import HTMLParser
import re
import sys

D3F = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
DEPRECATED_NAME_PREFIX = re.compile(r"^\[DEPRECATED\]\s*", re.IGNORECASE)
DEPRECATED_COMMENT = Literal("This technique has been deprecated.")


class DefinitionTextExtractor(HTMLParser):
    """Convert the limited HTML used in SPARTA definitions to readable text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.cells_in_row = 0

    def add_line_break(self):
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"br", "p", "div", "table", "thead", "tbody", "tr"}:
            self.add_line_break()
        if tag == "tr":
            self.cells_in_row = 0
        elif tag in {"th", "td"}:
            if self.cells_in_row:
                self.parts.append(": ")
            self.cells_in_row += 1
        elif tag == "li":
            self.add_line_break()
            self.parts.append("- ")

    def handle_endtag(self, tag):
        if tag.lower() in {"br", "p", "div", "table", "tr", "li"}:
            self.add_line_break()

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        lines = (" ".join(line.split()) for line in "".join(self.parts).splitlines())
        return "\n".join(line for line in lines if line)


def clean_definition(definition):
    """Strip presentation HTML from a SPARTA definition while retaining its text."""
    definition = "\n".join(line.rstrip() for line in definition.strip().splitlines())
    if not HTML_TAG.search(definition):
        return definition

    parser = DefinitionTextExtractor()
    parser.feed(definition)
    parser.close()
    return parser.text()


def is_deprecated(tech):
    """Detect standard STIX deprecation flags and SPARTA's name prefix."""
    return bool(
        tech.get("revoked", False)
        or tech.get("x_mitre_deprecated", False)
        or tech.get("x_sparta_deprecated", False)
        or DEPRECATED_NAME_PREFIX.match(tech["name"].strip())
    )


def clean_technique_name(name):
    """Remove SPARTA's deprecation marker from a display label."""
    return DEPRECATED_NAME_PREFIX.sub("", name.strip()).strip()


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


def sync_text_property(graph, sparta_uri, predicate, incoming_value):
    """
    Keep a single SPARTA text value for the given technique property.
    If the incoming value changed, replace the existing value.
    """
    incoming_literal = Literal(incoming_value.strip())
    existing_values = set(graph.objects(sparta_uri, predicate))

    if existing_values == {incoming_literal}:
        return

    graph.remove((sparta_uri, predicate, None))
    graph.add((sparta_uri, predicate, incoming_literal))


def sync_deprecation(graph, sparta_uri, deprecated):
    """Synchronize ATT&CK-style deprecation annotations for a SPARTA technique."""
    graph.remove((sparta_uri, OWL.deprecated, None))

    if deprecated:
        graph.add((sparta_uri, OWL.deprecated, Literal(True)))
        graph.add((sparta_uri, RDFS.comment, DEPRECATED_COMMENT))
    else:
        graph.remove((sparta_uri, RDFS.comment, DEPRECATED_COMMENT))


def add_technique_to_graph(g, tech, d3fend_graph):
    """
    Add a SPARTA Technique to the graph
    :param g: Graph
    :param tech: STIX attack-pattern object that is a SPARTA Technique
    :param d3fend_graph: Graph of D3FEND Ontology
    """
    sparta_id = get_sparta_id(tech)
    # If the technique has a SPARTA ID, add it to the graph
    if sparta_id is not None:
        # Create a URI for the SPARTA Technique
        sparta_uri = D3F[f"{sparta_id}"]
        technique_name = clean_technique_name(tech["name"])
        g.add((sparta_uri, RDF.type, OWL.Class))
        sync_text_property(
            d3fend_graph,
            sparta_uri,
            RDFS.label,
            technique_name + " - SPARTA",
        )
        sync_text_property(d3fend_graph, sparta_uri, SKOS.prefLabel, technique_name)
        sync_deprecation(d3fend_graph, sparta_uri, is_deprecated(tech))
        sparta_url = next(
            (
                ref.get("url")
                for ref in tech["external_references"]
                if ref.get("source_name") == "sparta"
            ),
            None,
        )
        g.add((sparta_uri, RDFS.seeAlso, URIRef(sparta_url)))
        sync_text_property(
            d3fend_graph,
            sparta_uri,
            D3F.definition,
            clean_definition(tech["description"]),
        )
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
        add_technique_to_graph(g, tech, d3fend_graph)

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
