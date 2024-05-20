from defusedxml.ElementTree import parse
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL

import sys


def get_capec_graph(capec_path):
    D3F = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")

    # Create a new graph
    g = Graph()

    # Load and parse the CAPEC XML file
    capec_tree = parse(capec_path)
    capec_root = capec_tree.getroot()

    # Extract and add CAPEC entries
    attack_patterns = capec_root.find("{http://capec.mitre.org/capec-3}Attack_Patterns")

    for attack_pattern in attack_patterns.findall(
        "{http://capec.mitre.org/capec-3}Attack_Pattern"
    ):
        capec_id = attack_pattern.attrib.get("ID")
        capec_name = attack_pattern.attrib.get("Name")
        capec_description = attack_pattern.find(
            "{http://capec.mitre.org/capec-3}Description"
        )
        capec_deprecated = (
            attack_pattern.attrib.get("Status") == "Deprecated"
            or attack_pattern.attrib.get("Status") == "Obsolete"
        )

        if capec_description.find("{http://www.w3.org/1999/xhtml}p") is not None:
            capec_description = capec_description.find(
                "{http://www.w3.org/1999/xhtml}p"
            ).text
        elif capec_description.text is not None:
            capec_description = capec_description.text

        capec_uri = D3F[f"CAPEC-{capec_id}"]
        g.add((capec_uri, RDF.type, D3F.CommonAttackPattern))
        g.add((capec_uri, RDF.type, OWL.NamedIndividual))
        g.add((capec_uri, RDF.type, OWL.Class))
        g.add((capec_uri, RDFS.label, Literal(capec_name)))
        g.add((capec_uri, RDFS.subClassOf, D3F.CommonAttackPattern))
        g.add(
            (
                capec_uri,
                RDFS.seeAlso,
                URIRef(f"https://capec.mitre.org/data/definitions/{capec_id}.html"),
            )
        )
        g.add((capec_uri, D3F["capec-id"], Literal(f"CAPEC-{capec_id}")))

        # Add definition if it is not empty
        if capec_description and not capec_deprecated:
            g.add((capec_uri, D3F.definition, Literal(capec_description)))

        if capec_deprecated:
            g.add((capec_uri, OWL.deprecated, Literal(True)))
            if capec_description:
                g.add((capec_uri, RDFS.comment, Literal(capec_description)))

        # Include relationships
        related_patterns = attack_pattern.findall(
            "{http://capec.mitre.org/capec-3}Related_Attack_Patterns/{http://capec.mitre.org/capec-3}Related_Attack_Pattern"
        )
        for related in related_patterns:
            related_id = related.attrib.get("CAPEC_ID")
            related_uri = D3F[f"CAPEC-{related_id}"]
            nature = related.attrib.get("Nature")

            if nature == "ParentOf":
                g.add((related_uri, RDFS.subClassOf, capec_uri))
                g.remove((related_uri, RDFS.subClassOf, D3F.CommonAttackPattern))
            elif nature == "ChildOf":
                g.add((capec_uri, RDFS.subClassOf, related_uri))
                g.remove((capec_uri, RDFS.subClassOf, D3F.CommonAttackPattern))
            elif nature == "PeerOf":
                g.add((capec_uri, D3F.related, related_uri))
                g.add((related_uri, D3F.related, capec_uri))

        # Add related CWE entries
        related_weaknesses = attack_pattern.findall(
            "{http://capec.mitre.org/capec-3}Related_Weaknesses/{http://capec.mitre.org/capec-3}Related_Weakness"
        )
        for related in related_weaknesses:
            cwe_id = related.attrib.get("CWE_ID")
            cwe_uri = D3F[f"CWE-{cwe_id}"]
            g.add((capec_uri, D3F.related, cwe_uri))

        # Add related ATT&CK techniques
        taxonomy_mappings = attack_pattern.findall(
            "{http://capec.mitre.org/capec-3}Taxonomy_Mappings/{http://capec.mitre.org/capec-3}Taxonomy_Mapping"
        )
        for mapping in taxonomy_mappings:
            taxonomy_name = mapping.attrib.get("Taxonomy_Name")
            if taxonomy_name == "ATTACK":
                attack_uri = D3F[
                    f"T{mapping.find('{http://capec.mitre.org/capec-3}Entry_ID').text}"
                ]
                g.add((capec_uri, D3F.related, attack_uri))

    return g


def main(CAPEC_VERSION="3.9"):

    d3fend_graph = Graph()
    d3fend_graph.parse("src/ontology/d3fend-protege.capec.ttl")

    capec_graph = get_capec_graph(f"data/capec_v{CAPEC_VERSION}.xml")

    d3fend_graph += capec_graph

    d3fend_graph.serialize(
        destination="src/ontology/d3fend-protege.capec.ttl", format="turtle"
    )


if __name__ == "__main__":
    version = sys.argv[1]
    main(CAPEC_VERSION=version)
