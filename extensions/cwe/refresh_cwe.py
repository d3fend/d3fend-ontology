"""Refresh source-owned CWE text annotations before merging an import."""

import argparse

from rdflib import Graph, Namespace, RDFS


D3F = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")
SINGLE_VALUE_PROPERTIES = (RDFS.label, D3F.definition)


def refresh_cwe_text(graph, incoming):
    """Replace imported names and definitions; retain curated relationships."""
    replacements = {}
    for subject in set(incoming.subjects()):
        if not str(subject).startswith(f"{D3F}CWE-"):
            continue
        for predicate in SINGLE_VALUE_PROPERTIES:
            values = set(incoming.objects(subject, predicate))
            if len(values) > 1:
                raise ValueError(f"Multiple incoming values for {subject} {predicate}")
            if values:
                replacements[subject, predicate] = next(iter(values))

    for (subject, predicate), value in replacements.items():
        graph.set((subject, predicate, value))

    return graph


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ontology", help="Existing D3FEND Turtle file")
    parser.add_argument("incoming", help="Generated CWE N-Triples file")
    parser.add_argument("output", help="Updated Turtle file")
    args = parser.parse_args()

    graph = Graph().parse(args.ontology, format="turtle")
    incoming = Graph().parse(args.incoming, format="nt")
    refresh_cwe_text(graph, incoming).serialize(
        destination=args.output, format="turtle"
    )


if __name__ == "__main__":
    main()
