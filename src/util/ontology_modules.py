#!/usr/bin/env python3
"""Assemble local Turtle ontology modules through an explicit XML catalog."""

from __future__ import annotations

import argparse
from pathlib import Path
from urllib.parse import unquote, urlsplit

from defusedxml import ElementTree as ET
from rdflib import Graph
from rdflib.namespace import OWL, RDF
from ttlser import CustomTurtleSerializer


DEFAULT_SOURCE = Path("src/ontology/d3fend-protege.ttl")
CATALOG_NAMESPACE = "{urn:oasis:names:tc:entity:xmlns:xml:catalog}"


class AssertedTurtleSerializer(CustomTurtleSerializer):
    """Keep asserted triple direction instead of normalizing symmetric axioms."""

    symmetric_predicates = ()


def read_catalog(catalog_path):
    """Read explicit ontology-IRI mappings to files beside the catalog."""
    catalog_path = Path(catalog_path).resolve()
    mappings = {}
    for entry in ET.parse(catalog_path).getroot().iter(f"{CATALOG_NAMESPACE}uri"):
        name, location = entry.get("name"), entry.get("uri")
        if not name or not location:
            raise ValueError(f"Catalog entry needs name and uri: {catalog_path}")
        uri = urlsplit(location)
        if uri.scheme or uri.netloc or uri.query or uri.fragment:
            raise ValueError(f"Catalog mapping must be a local file path: {location}")
        path = (catalog_path.parent / unquote(uri.path)).resolve()
        if name in mappings and mappings[name] != path:
            raise ValueError(f"Conflicting catalog mappings for {name}")
        mappings[name] = path
    return mappings


def load_ontology(source_path=DEFAULT_SOURCE, catalog_path=None):
    """Load Turtle imports locally, preserving the root ontology's metadata.

    Each file is parsed separately so blank-node labels remain scoped to that
    document. Imports must have explicit catalog mappings; import IRIs are never
    fetched. The result omits import declarations and imported ontology headers,
    while retaining all other RDF statements without OWL re-interpretation.
    """
    source_path = Path(source_path).resolve()
    catalog_path = (
        Path(catalog_path).resolve()
        if catalog_path is not None
        else source_path.with_name("catalog-v001.xml")
    )
    mappings = None
    visited = set()
    result = Graph()

    def visit(path, is_root=False):
        nonlocal mappings
        if path in visited:
            return
        visited.add(path)
        graph = Graph().parse(
            data=path.read_text(encoding="utf-8"),
            format="turtle",
            publicID=path.as_uri(),
        )
        imports = sorted(set(graph.objects(None, OWL.imports)), key=str)
        if imports and mappings is None:
            if not catalog_path.is_file():
                raise ValueError(f"Imports require a local catalog: {catalog_path}")
            mappings = read_catalog(catalog_path)
        for ontology_iri in imports:
            imported_path = mappings.get(str(ontology_iri))
            if imported_path is None:
                raise ValueError(
                    f"No catalog mapping for import {ontology_iri} in {path}"
                )
            if not imported_path.is_file():
                raise FileNotFoundError(
                    f"Missing file for import {ontology_iri}: {imported_path}"
                )
            visit(imported_path)

        headers = set() if is_root else set(graph.subjects(RDF.type, OWL.Ontology))
        for prefix, namespace in graph.namespaces():
            result.bind(prefix, namespace)
        for subject, predicate, obj in graph:
            if predicate != OWL.imports and subject not in headers:
                result.add((subject, predicate, obj))

    visit(source_path, is_root=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    graph = load_ontology(args.source, args.catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    serializer = AssertedTurtleSerializer(graph)
    # Keep RDF list order, including lists referenced by annotated OWL axioms.
    serializer.no_reorder_list = set(graph.predicates()) | set(
        graph.objects(None, OWL.annotatedProperty)
    )
    with args.output.open("wb") as stream:
        serializer.serialize(stream)
    print(f"Assembled {len(graph)} triples into {args.output}")


if __name__ == "__main__":
    main()
