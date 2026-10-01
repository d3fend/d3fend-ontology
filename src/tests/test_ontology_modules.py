"""Regression checks for local, lossless ontology module assembly."""

import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF, RDFS

from src.util.dashboard_report import parse_graph, select_source
from src.util.ontology_modules import load_ontology, main, read_catalog


D3F = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")
ROOT = URIRef("http://d3fend.mitre.org/ontologies/d3fend.owl")
MODULE = Namespace("http://d3fend.mitre.org/ontologies/modules/")
PREFIXES = """
@prefix d3f: <http://d3fend.mitre.org/ontologies/d3fend.owl#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
"""


class OntologyModulesTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def write(self, name, turtle):
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(PREFIXES + turtle, encoding="utf-8")
        return path

    def catalog(self, mappings):
        entries = "\n".join(
            f'<uri name="{iri}" uri="{path}"/>' for iri, path in mappings.items()
        )
        path = self.directory / "catalog-v001.xml"
        path.write_text(
            '<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">'
            + entries
            + "</catalog>",
            encoding="utf-8",
        )
        return path

    def root(self, imports):
        import_statement = (
            "; owl:imports " + ", ".join(f"<{iri}>" for iri in imports)
            if imports
            else ""
        )
        return self.write(
            "root.ttl",
            f'<{ROOT}> a owl:Ontology ; rdfs:label "Root metadata"'
            f"{import_statement} .\n"
            'd3f:Entity a owl:Class ; d3f:definition "Retained annotation" .',
        )

    def test_nested_and_cyclic_imports_preserve_root_metadata(self):
        source = self.root([MODULE.events])
        self.write(
            "modules/events.ttl",
            f'<{MODULE.events}> a owl:Ontology ; rdfs:label "Module metadata" ; '
            f"owl:imports <{MODULE.core}> .\n"
            "d3f:Event a owl:Class ; rdfs:subClassOf d3f:Entity .",
        )
        self.write(
            "modules/core.ttl",
            f"<{MODULE.core}> a owl:Ontology ; owl:imports <{ROOT}> .\n"
            'd3f:Entity rdfs:label "Entity" .',
        )
        self.catalog(
            {
                MODULE.events: "modules/events.ttl",
                MODULE.core: "modules/core.ttl",
                ROOT: "root.ttl",
            }
        )

        graph = load_ontology(source)

        self.assertEqual(set(graph.subjects(RDF.type, OWL.Ontology)), {ROOT})
        self.assertIn((ROOT, RDFS.label, Literal("Root metadata")), graph)
        self.assertIn((D3F.Entity, RDFS.label, Literal("Entity")), graph)
        self.assertIn((D3F.Event, RDFS.subClassOf, D3F.Entity), graph)
        self.assertIn(
            (D3F.Entity, D3F.definition, Literal("Retained annotation")), graph
        )
        self.assertFalse(list(graph.triples((None, OWL.imports, None))))
        self.assertFalse(list(graph.triples((MODULE.events, None, None))))

    def test_missing_import_mapping_fails_without_network_fallback(self):
        source = self.root([MODULE.missing])
        self.catalog({})

        with self.assertRaisesRegex(ValueError, "No catalog mapping for import"):
            load_ontology(source)

    def test_missing_catalog_fails(self):
        source = self.root([MODULE.missing])

        with self.assertRaisesRegex(ValueError, "Imports require a local catalog"):
            load_ontology(source)

    def test_remote_catalog_mapping_is_rejected(self):
        source = self.root([MODULE.events])
        self.catalog({MODULE.events: "https://example.invalid/events.ttl"})

        with self.assertRaisesRegex(ValueError, "must be a local file path"):
            load_ontology(source)

    def test_missing_mapped_file_fails(self):
        source = self.root([MODULE.events])
        self.catalog({MODULE.events: "missing.ttl"})

        with self.assertRaisesRegex(FileNotFoundError, "Missing file for import"):
            load_ontology(source)

    def test_blank_nodes_and_rdf_lists_are_preserved_with_document_scope(self):
        source = self.root([MODULE.first, MODULE.second])
        expected = Graph().parse(source, format="turtle")
        expected.remove((None, OWL.imports, None))
        for name in ("first", "second"):
            ontology_iri = MODULE[name]
            path = self.write(
                f"{name}.ttl",
                f"<{ontology_iri}> a owl:Ontology .\n"
                f"d3f:{name} a owl:Class ; rdfs:subClassOf _:restriction .\n"
                "_:restriction a owl:Restriction ; owl:onProperty d3f:has-part ;\n"
                "    owl:someValuesFrom _:union .\n"
                "_:union owl:unionOf _:list .\n"
                f"_:list rdf:first d3f:{name}Part ; rdf:rest rdf:nil .",
            )
            module = Graph().parse(path, format="turtle")
            module.remove((ontology_iri, None, None))
            expected += module
        self.catalog({MODULE.first: "first.ttl", MODULE.second: "second.ttl"})

        graph = load_ontology(source)

        self.assertTrue(isomorphic(graph, expected))
        first = graph.value(D3F.first, RDFS.subClassOf)
        second = graph.value(D3F.second, RDFS.subClassOf)
        self.assertNotEqual(first, second)
        self.assertEqual(len(list(graph.subjects(RDF.type, OWL.Restriction))), 2)

    def test_flat_ontology_needs_no_catalog(self):
        source = self.root([])

        self.assertTrue(
            isomorphic(load_ontology(source), Graph().parse(source, format="turtle"))
        )

    def test_dashboard_fallback_and_explicit_source_load_modules(self):
        source = self.root([MODULE.events])
        self.write(
            "events.ttl",
            f"<{MODULE.events}> a owl:Ontology .\nd3f:Event a owl:Class .",
        )
        self.catalog({MODULE.events: "events.ttl"})

        with patch("src.util.dashboard_report.DEFAULT_SOURCE_PATHS", (str(source),)):
            fallback = parse_graph(select_source(None))
        explicit = parse_graph(select_source(str(source)))

        self.assertIn((D3F.Event, RDF.type, OWL.Class), fallback)
        self.assertTrue(isomorphic(fallback, explicit))

    def test_cli_serialization_is_repeatable_and_preserves_rdf(self):
        source = self.root([MODULE.events])
        self.write(
            "events.ttl",
            f"<{MODULE.events}> a owl:Ontology .\n"
            "d3f:Z owl:disjointWith d3f:A .\n"
            "d3f:Event rdfs:subClassOf [ a owl:Restriction ;\n"
            "    owl:onProperty d3f:has-part ;\n"
            "    owl:someValuesFrom [ owl:unionOf (d3f:B d3f:A) ] ] .",
        )
        self.catalog({MODULE.events: "events.ttl"})
        outputs = []
        for index in range(2):
            output = self.directory / f"output-{index}.ttl"
            with patch(
                "sys.argv",
                [
                    "ontology_modules.py",
                    "--source",
                    str(source),
                    "--output",
                    str(output),
                ],
            ):
                main()
            outputs.append(output.read_bytes())

        self.assertEqual(*outputs)
        self.assertTrue(
            isomorphic(
                load_ontology(source),
                Graph().parse(data=outputs[0], format="turtle"),
            )
        )


class RepositoryOntologyModulesTest(unittest.TestCase):
    def test_catalog_closure_module_identity_and_entity_ownership(self):
        ontology_dir = Path(__file__).resolve().parents[1] / "ontology"
        source = ontology_dir / "d3fend-protege.ttl"
        catalog = read_catalog(ontology_dir / "catalog-v001.xml")
        initiative_catalog = read_catalog(
            ontology_dir / "initiatives" / "catalog-v001.xml"
        )
        for ontology_iri, path in catalog.items():
            self.assertEqual(initiative_catalog.get(ontology_iri), path)
        module_paths = set(ontology_dir.glob("modules/*.ttl")) | set(
            ontology_dir.glob("external/*.ttl")
        )
        self.assertTrue(module_paths)
        expected_modules = {
            URIRef(
                "http://d3fend.mitre.org/ontologies/"
                + path.relative_to(ontology_dir).with_suffix("").as_posix()
            ): path
            for path in module_paths
        }
        self.assertEqual(catalog[str(ROOT)], source)
        for ontology_iri, path in expected_modules.items():
            self.assertEqual(catalog[str(ontology_iri)], path)

        declarations = {
            OWL.Class,
            OWL.NamedIndividual,
            OWL.ObjectProperty,
            OWL.DatatypeProperty,
            OWL.AnnotationProperty,
            RDF.Property,
            RDFS.Datatype,
        }
        module_prefixes = (
            "http://d3fend.mitre.org/ontologies/modules/",
            "http://d3fend.mitre.org/ontologies/external/",
        )
        substantive_owners = defaultdict(set)
        visited = set()
        pending = [ROOT]
        while pending:
            ontology_iri = pending.pop()
            if ontology_iri in visited:
                continue
            visited.add(ontology_iri)
            path = catalog[str(ontology_iri)]
            graph = Graph().parse(path, format="turtle")
            self.assertEqual(
                set(graph.subjects(RDF.type, OWL.Ontology)), {ontology_iri}
            )
            pending.extend(graph.objects(ontology_iri, OWL.imports))
            for term in set(graph.all_nodes()) | set(graph.predicates()):
                if isinstance(term, URIRef) and str(term).startswith(module_prefixes):
                    self.assertIn(term, expected_modules)
            for subject, predicate, obj in graph:
                if not isinstance(subject, URIRef) or subject == ontology_iri:
                    continue
                self.assertNotEqual(ontology_iri, ROOT, "Root must only import modules")
                # OWLAPI may repeat bare declarations of referenced sibling entities.
                # Definition text, axioms, and assertions must retain one owner.
                if predicate == RDF.type and obj in declarations:
                    continue
                substantive_owners[subject].add(path.relative_to(ontology_dir))

        self.assertEqual(visited, {ROOT, *expected_modules})
        self.assertTrue(substantive_owners)
        duplicate_owners = {
            str(entity): sorted(map(str, owners))
            for entity, owners in substantive_owners.items()
            if len(owners) > 1
        }
        self.assertEqual(
            duplicate_owners, {}, "Entities have multiple substantive owners"
        )


if __name__ == "__main__":
    unittest.main()
