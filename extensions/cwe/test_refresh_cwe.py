import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import Graph, Literal, RDFS, SKOS

from refresh_cwe import D3F, main, refresh_cwe_text


class RefreshCWETests(unittest.TestCase):
    def test_refresh_repairs_duplicates_and_preserves_curated_facts(self):
        subject = D3F["CWE-1039"]
        graph = Graph()
        graph.add((subject, RDFS.label, Literal("Old name")))
        graph.add((subject, RDFS.label, Literal("Current name")))
        graph.add((subject, SKOS.altLabel, Literal("Curated alternate")))
        graph.add((subject, D3F.definition, Literal("Old definition")))
        graph.add((subject, D3F.definition, Literal("Another old definition")))
        curated = (subject, RDFS.subClassOf, D3F["CWE-693"])
        mapping = (D3F.FileAnalysis, D3F.related, subject)
        local = (D3F.CreateProcess, D3F.definition, Literal("Local definition"))
        for triple in (curated, mapping, local):
            graph.add(triple)
        incoming = Graph()
        incoming.add((subject, RDFS.label, Literal("Current name")))
        incoming.add((subject, D3F.definition, Literal("Current definition")))
        incoming.add((subject, D3F.synonym, Literal("Imported synonym")))
        incoming.add((D3F["CWE-1188"], RDFS.label, Literal("New entry")))

        refresh_cwe_text(graph, incoming)
        graph += incoming

        self.assertEqual(
            set(graph.objects(subject, RDFS.label)), {Literal("Current name")}
        )
        self.assertEqual(
            set(graph.objects(subject, D3F.definition)), {Literal("Current definition")}
        )
        self.assertEqual(
            set(graph.objects(subject, SKOS.altLabel)), {Literal("Curated alternate")}
        )
        self.assertNotIn((subject, SKOS.altLabel, Literal("Old name")), graph)
        for triple in (curated, mapping, local):
            self.assertIn(triple, graph)
        self.assertIn((subject, D3F.synonym, Literal("Imported synonym")), graph)
        self.assertIn((D3F["CWE-1188"], RDFS.label, Literal("New entry")), graph)
        first_update = set(graph)
        refresh_cwe_text(graph, incoming)
        graph += incoming
        self.assertEqual(set(graph), first_update)

    def test_ambiguous_import_is_rejected_before_changing_graph(self):
        for predicate in (RDFS.label, D3F.definition):
            with self.subTest(predicate=predicate):
                graph = Graph()
                graph.add((D3F["CWE-1039"], RDFS.label, Literal("Existing")))
                original = set(graph)
                incoming = Graph()
                incoming.add((D3F["CWE-1188"], RDFS.label, Literal("Valid")))
                incoming.add((D3F["CWE-1039"], predicate, Literal("First")))
                incoming.add((D3F["CWE-1039"], predicate, Literal("Second")))
                with self.assertRaises(ValueError):
                    refresh_cwe_text(graph, incoming)
                self.assertEqual(set(graph), original)

    def test_command_line_reads_and_updates_the_same_ontology_file(self):
        with tempfile.TemporaryDirectory() as directory:
            ontology = Path(directory) / "ontology.ttl"
            incoming_path = Path(directory) / "incoming.nt"
            graph = Graph()
            graph.add((D3F["CWE-1039"], RDFS.label, Literal("Old name")))
            graph.serialize(destination=ontology, format="turtle")
            incoming = Graph()
            incoming.add((D3F["CWE-1039"], RDFS.label, Literal("Current name")))
            incoming.serialize(destination=incoming_path, format="nt", encoding="utf-8")
            arguments = [
                "refresh_cwe.py",
                str(ontology),
                str(incoming_path),
                str(ontology),
            ]
            with patch.object(sys, "argv", arguments):
                main()
            updated = Graph().parse(ontology, format="turtle")
            self.assertEqual(
                set(updated.objects(D3F["CWE-1039"], RDFS.label)),
                {Literal("Current name")},
            )
            self.assertNotIn(
                (D3F["CWE-1039"], SKOS.altLabel, Literal("Old name")), updated
            )


if __name__ == "__main__":
    unittest.main()
