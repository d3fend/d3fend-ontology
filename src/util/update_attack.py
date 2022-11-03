import string
import json
import re
import csv
import sys
from pathlib import Path

from rdflib import URIRef, Literal
from build import get_graph, _xmlns


D3F_PREFIX = "d3f:"
ENTERPRISE_ATTACK_JSON = "enterprise-attack-11.2.json"


def recursive_extract(dictionary, key):
    if not isinstance(dictionary, dict):
        print(dictionary)
        print("is not dict")
        return
    for k, v in dictionary.items():
        if k == key:
            yield v
        if isinstance(v, dict):
            recursive_extract(v, key)


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


def get_mitre_attacks(stix):
    """Get all attack-patterns where the source_name is a mitre-attack"""
    for attack_pattern in filter(
        lambda x: x["type"] == "attack-pattern", stix["objects"]
    ):
        for mitre_attack in filter(
            lambda x: x["source_name"] == "mitre-attack",
            attack_pattern["external_references"],
        ):
            yield attack_pattern, mitre_attack


def test_get_mitre_attacks():
    stix = get_stix()
    for attack_pattern, mitre_attack in get_mitre_attacks(stix):
        raise NotImplementedError


if __name__ == "__main__":
    g = get_graph(filename="src/ontology/d3fend-protege.ttl")
    stix = get_stix()

    attack_ids = set()
    deprecated_attack_ids = set()
    count_deprecated = 0  # total, could have duplicates...
    technique_meta = {}
    for o, r in get_mitre_attacks(stix):
        if re.match("^T[0-9]", r["external_id"]):  # ensure we are getting techniques...
            attack_id = r["external_id"]
            technique_meta[attack_id] = {"name": o["name"]}

            if "." in attack_id:  # subtechniques go under techniques...
                superclasses = [D3F_PREFIX + attack_id.split(".")[0]]
            else:
                superclasses = [
                    kcp_to_class(p["phase_name"]) for p in o["kill_chain_phases"]
                ]
            technique_meta[attack_id]["superclasses"] = superclasses

            if o.get("x_mitre_deprecated", None) is True:
                technique_meta[attack_id]["deprecated"] = True
                deprecated_attack_ids.add(attack_id)
                count_deprecated += 1
            else:
                technique_meta[attack_id]["deprecated"] = False
                attack_ids.add(attack_id)

    attack_ids = list(attack_ids)

    incount = 0
    nincount = 0
    present = set()
    missing = set()
    for attack_id in attack_ids:
        # import ipdb; ipdb.set_trace()
        if (
            URIRef(_xmlns + attack_id),
            URIRef(_xmlns + "attack-id"),
            Literal(attack_id),
        ) in g:
            incount += 1
            present.add(attack_id)
        else:
            nincount += 1
            missing.add(attack_id)

    dincount = 0
    dnincount = 0
    deprecated_in_d3 = set()
    for attack_id in deprecated_attack_ids:
        # import ipdb; ipdb.set_trace()
        if (
            URIRef(_xmlns + attack_id),
            URIRef(_xmlns + "attack-id"),
            Literal(attack_id),
        ) in g:
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
                    technique_meta[attack_id]["name"],
                    "|".join(technique_meta[attack_id]["superclasses"]),
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
