import string
import json
import re
import csv
import sys
from pathlib import Path

from rdflib import URIRef, Literal, Graph, RDFS
from build import get_graph, _xmlns as _XMLNS


D3F_PREFIX = "d3f:"
ENTERPRISE_ATTACK_JSON = "enterprise-attack-11.2.json"


def kcp_to_class(kcp):
    return str(
        D3F_PREFIX + string.capwords(kcp.replace("-", " ")) + " Technique"
    ).replace(" ", "")


def report_writer(filename, list_of_things):
    with open(filename, "+w") as f:
        for line in list_of_things:
            f.write(f"{line}\n")


def _print(*args):
    print(" ".join([str(a) for a in args]).rjust(80, " "))
    print()


def get_stix():
    enterprise_attack = Path(f"data/{ENTERPRISE_ATTACK_JSON}")
    if not enterprise_attack.exists():
        print("please run: make download-attack", enterprise_attack.absolute())
        sys.exit(1)

    return json.loads(enterprise_attack.read_text())


def get_mitre_attack_techniques(stix):
    """Get all attack-patterns where the source_name is a mitre-attack.

    An attack-pattern has a set of external_references that describe
    specific attacks, e.g.:

    { ...,
      'external_references': [{
        'external_id': 'T1055.011',
        'source_name': 'mitre-attack',
        'url': 'https://attack.mitre.org/techniques/T1055/011'
        },...
        ]
    }

    """
    RE_ATTACK_TECHNIQUE = re.compile("^T[0-9]")
    for attack_pattern in (x for x in stix["objects"] if x["type"] == "attack-pattern"):
        for mitre_attack in (
            y
            for y in attack_pattern["external_references"]
            if y["source_name"] == "mitre-attack"
        ):
            if RE_ATTACK_TECHNIQUE.match(
                mitre_attack["external_id"]
            ):  # ensure we are getting techniques...
                yield attack_pattern, mitre_attack


def _assert(actual, expected):
    if expected != actual:
        raise AssertionError(f"expected: {expected} != actual: {actual}")


def test_get_mitre_attacks():
    stix = get_stix()
    for attack_pattern, mitre_attack in get_mitre_attack_techniques(stix):
        _assert(attack_pattern["type"], "attack-pattern")
        _assert(mitre_attack["source_name"], "mitre-attack")
        _assert(mitre_attack["external_id"].startswith("T"), True)


def get_attacks(stix):
    """Get all attack-patterns where the source_name is a mitre-attack.

    An attack metadata has the following structure:

    {
        "T1055.011": {
            "name": "Extra Window Memory Injection",
            "deprecated": False,
            "superclasses": ["d3f:T1055"],
            },
        "T1055": {
            "name": "Process Injection",
            "deprecated": False,
            "superclasses": [
                "d3f:DefenseEvasionTechnique",
                "d3f:PrivilegeEscalationTechnique",
            ],
            }
    }
    """
    attack_ids = set()
    deprecated_attack_ids = set()
    count_deprecated = 0  # total, could have duplicates...
    techniques_metadata = {}
    for o, r in get_mitre_attack_techniques(stix):
        attack_id = r["external_id"]
        techniques_metadata[attack_id] = {"name": o["name"]}

        if "." in attack_id:  # subtechniques go under techniques...
            superclasses = [D3F_PREFIX + attack_id.split(".")[0]]
        else:
            superclasses = [
                kcp_to_class(p["phase_name"]) for p in o["kill_chain_phases"]
            ]
        techniques_metadata[attack_id]["superclasses"] = superclasses

        if o.get("x_mitre_deprecated", None) is True:
            techniques_metadata[attack_id]["deprecated"] = True
            deprecated_attack_ids.add(attack_id)
            count_deprecated += 1
        else:
            techniques_metadata[attack_id]["deprecated"] = False
            attack_ids.add(attack_id)
    return attack_ids, deprecated_attack_ids, techniques_metadata, count_deprecated


def test_get_attacks():
    stix = get_stix()
    attack_ids, deprecated_attack_ids, techniques_metadata = get_attacks(stix)
    _assert(len(attack_ids) + len(deprecated_attack_ids), len(techniques_metadata))
    _assert(len(attack_ids), 707)
    _assert(len(deprecated_attack_ids), 12)
    _assert(len(techniques_metadata), 719)
    _assert(techniques_metadata["T1055.011"]["name"], "Extra Window Memory Injection")
    _assert(techniques_metadata["T1055.011"]["deprecated"], False)
    _assert(
        techniques_metadata["T1055.011"]["superclasses"],
        ["d3f:T1055"],
    )
    _assert(techniques_metadata["T1055"]["deprecated"], False)
    _assert(
        techniques_metadata["T1055"]["superclasses"],
        ["d3f:DefenseEvasionTechnique", "d3f:PrivilegeEscalationTechnique"],
    )


def test_update_attack_labels():
    """
    Replace an rdfs:label when changed in the attack.json file.

    :T1001.001 a owl:Class ;
        rdfs:label "Junk Data" ;
        rdfs:subClassOf :T1001 ;
        :attack-id "T1001.001" .

    """
    techniques_meta = {
        "T1055.011": {
            "name": "BRAND NEW NAME",
            "deprecated": False,
            "superclasses": ["d3f:T1055"],
        }
    }
    g = Graph()
    g.parse(
        data="""
    @prefix : <http://d3fend.mitre.org/ontologies/d3fend.owl#> .
    @prefix dcterms: <http://purl.org/dc/terms/> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    :T1054 a owl:Class ;
    rdfs:label "Indicator Blocking" ;
    rdfs:subClassOf :DefenseEvasionTechnique ;
    :attack-id "T1054" .

    :T1055 a owl:Class ;
        rdfs:label "Process Injection" ;
        rdfs:subClassOf :DefenseEvasionTechnique,
            :PrivilegeEscalationTechnique ;
        :attack-id "T1055" .

    :T1055.001 a owl:Class ;
        rdfs:label "Dynamic-link Library Injection" ;
        rdfs:subClassOf :T1055,
            [ a owl:Restriction ;
                owl:onProperty :adds ;
                owl:someValuesFrom :SharedLibraryFile ],
            [ a owl:Restriction ;
                owl:onProperty :invokes ;
                owl:someValuesFrom :SystemCall ],
            [ a owl:Restriction ;
                owl:onProperty :loads ;
                owl:someValuesFrom :SharedLibraryFile ] ;
        :attack-id "T1055.001" .
    """,
        format="turtle",
    )
    update_attack_labels(g, techniques_meta)
    _assert(
        g.value(URIRef(_XMLNS + "T1055.011"), RDFS.label), Literal("BRAND NEW NAME")
    )


def update_attack_labels(d3fend_graph, techniques_meta):
    """
    Update the graph with the new techniques metadata.
    """
    for attack_id, meta in techniques_meta.items():
        attack_uri = URIRef(_XMLNS + attack_id)
        current_label = d3fend_graph.value(attack_uri, RDFS.label)
        if current_label != meta["name"]:
            d3fend_graph.remove((attack_uri, RDFS.label, current_label))
            d3fend_graph.add((attack_uri, RDFS.label, Literal(meta["name"])))


def main():
    d3fend_graph = get_graph(filename="src/ontology/d3fend-protege.ttl")
    stix = get_stix()

    (
        attack_ids,
        deprecated_attack_ids,
        techniques_metadata,
        count_deprecated,
    ) = get_attacks(stix)
    attack_ids = list(attack_ids)

    incount = 0
    nincount = 0
    present = set()
    missing = set()
    for attack_id in attack_ids:
        if (
            URIRef(_XMLNS + attack_id),
            URIRef(_XMLNS + "attack-id"),
            Literal(attack_id),
        ) in d3fend_graph:
            incount += 1
            present.add(attack_id)
        else:
            nincount += 1
            missing.add(attack_id)

    dincount = 0
    dnincount = 0
    deprecated_in_d3 = set()
    for attack_id in deprecated_attack_ids:
        if (
            URIRef(_XMLNS + attack_id),
            URIRef(_XMLNS + "attack-id"),
            Literal(attack_id),
        ) in d3fend_graph:
            dincount += 1
            deprecated_in_d3.add(attack_id)
        else:
            dnincount += 1

    _print("Valid ATT&CK ids found in stix document:", len(attack_ids))

    _print("Valid ATT&CK ids in D3FEND graph:", incount)

    _print("Valid ATT&CK ids not in D3FEND graph: ", nincount)
    report_writer("reports/attack_update-missing_attack_ids.txt", sorted(list(missing)))

    outfile_csv = Path("reports/attack_update-missing_attack_ids-robot_template.csv")
    with outfile_csv.open("w") as f:
        # csvwriter = csv.writer(f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        # csvwriter = csv.writer(f)
        csvwriter = csv.writer(
            f, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )
        # ID & LABEL are reserved words in robot template command, both are required
        # to be unique. ID is unique, however, rdfs:label is never expected to be unique in D3FEND.
        csvwriter.writerow(["id", "name", "SC", "attack id"])
        # see docs for explanation   http://robot.obolibrary.org/template
        # csvwriter.writerow(["ID", "A rdfs:label", "AI rdfs:subClassOf SPLIT=|", "A " + D3F_PREFIX + "attack-id"])
        csvwriter.writerow(
            ["ID", "A rdfs:label", "SC % SPLIT=|", "A " + D3F_PREFIX + "attack-id"]
        )
        # csvwriter.writerow(['ID', 'LABEL', 'SC'])
        for attack_id in sorted(missing):
            if "." in attack_id:
                superclass = D3F_PREFIX + attack_id.split(".")[0]
            else:
                superclass = D3F_PREFIX + "TODO"
            csvwriter.writerow(
                [
                    D3F_PREFIX + attack_id,
                    techniques_metadata[attack_id]["name"],
                    "|".join(techniques_metadata[attack_id]["superclasses"]),
                    attack_id,
                ]
            )

    _print("Deprecated ATT&CK total:", count_deprecated)

    _print("Deprecated ATT&CK deduped:", len(deprecated_attack_ids))

    _print("Deprecated ATT&CK ids in D3FEND:", dnincount)
    report_writer(
        "reports/attack_update-deprecated_attack_in_d3fend.txt",
        sorted(list(deprecated_in_d3)),
    )


if __name__ == "__main__":
    main()
