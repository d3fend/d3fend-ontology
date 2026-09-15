import json
import re
from pathlib import Path

from rdflib import BNode, Graph

PUBLIC_ONTOLOGY_FILEPATH = "build/d3fend-public-with-controls.ttl"
PUBLIC_DEST_DIR = "build/"

GENERATED_BNODE = re.compile(r"^n[0-9a-f]{32}b([1-9][0-9]*)$")

DEFAULT_CONTEXT = {
    "d3f": "http://d3fend.mitre.org/ontologies/d3fend.owl#",
    "dbr": "http://dbpedia.org/resource/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


class colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def log(message, error=False, info=False):
    if error:
        print(colors.FAIL + message)
    elif info:
        print(colors.OKBLUE + message)
    else:
        print(colors.OKGREEN + message)


def get_graph(filename=PUBLIC_ONTOLOGY_FILEPATH):
    g = Graph()
    g.parse(filename)
    log(filename)
    log(f"The graph has {len(g)} triples", info=True)
    return g


def stable_bnode(term):
    if not isinstance(term, BNode):
        return term
    match = GENERATED_BNODE.fullmatch(str(term))
    if not match:
        raise ValueError(f"Unexpected blank-node identifier: {term}")
    return BNode(f"b{int(match.group(1)):04d}")


def normalize_jsonld(value, parent_key=None):
    if isinstance(value, dict):
        return {key: normalize_jsonld(item, key) for key, item in value.items()}
    if isinstance(value, list):
        items = [normalize_jsonld(item) for item in value]
        if parent_key in {"@context", "@list"}:
            return items
        return sorted(
            items,
            key=lambda item: json.dumps(
                item, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ),
        )
    return value


def serialize_jsonld(graph):
    stable_graph = Graph()
    for triple in graph:
        stable_graph.add(tuple(stable_bnode(term) for term in triple))
    document = json.loads(
        stable_graph.serialize(format="json-ld", context=DEFAULT_CONTEXT)
    )
    return (
        json.dumps(
            normalize_jsonld(document), indent=2, sort_keys=True, ensure_ascii=False
        )
        + "\n"
    )


if __name__ == "__main__":
    output_fname = "d3fend-public-with-controls"

    g = get_graph()
    destination = Path(f"{PUBLIC_DEST_DIR}{output_fname}.json")
    destination.write_text(
        serialize_jsonld(g),
        encoding="utf-8",
    )

    log(f"wrote: {output_fname}.json")

    log(f"The graph now has {len(g)} triples", info=True)
