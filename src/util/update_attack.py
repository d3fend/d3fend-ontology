import json
import re

from rdflib import URIRef, Literal
from build import get_graph, _xmlns

g = get_graph(filename="src/ontology/d3fend-protege.ttl")


def recursive_extract(dictionary, key):
    if type(dictionary) != dict:
        print(dictionary)
        print("is not dict")
        return
    for k, v in dictionary.items():
        if k == key:
            yield v
        if type(v) == dict:
            recursive_extract(v, key)


with open("data/enterprise-attack-11.2.json") as f:
    stix = json.loads(f.read())

attack_ids = set()
deprecated_attack_ids = set()
count_deprecated = 0  # total, could have duplicates...
for o in stix["objects"]:
    if "external_references" in o:
        for r in o["external_references"]:
            if r.get("source_name", None) == "mitre-attack":
                if "external_id" in r:
                    if re.match("^T[0-9]", r["external_id"]):
                        if o.get("x_mitre_deprecated", None) is True:
                            deprecated_attack_ids.add(r["external_id"])
                            count_deprecated += 1
                        else:
                            attack_ids.add(r["external_id"])


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


def report_writer(filename, list_of_things):
    with open(filename, "+w") as f:
        for line in list_of_things:
            f.write(str(line) + "\n")


def _print(*args):
    print(" ".join([str(a) for a in args]).rjust(80, " "))
    print()


_print("Valid ATT&CK ids found in stix document:", len(attack_ids))

_print("Valid ATT&CK ids in D3FEND graph:", incount)

_print("Valid ATT&CK ids not in D3FEND graph: ", nincount)
report_writer("reports/attack_update-missing_attack_ids.txt", list(missing))

_print("Deprecated ATT&CK total:", count_deprecated)

_print("Deprecated ATT&CK deduped:", len(deprecated_attack_ids))

_print("Deprecated ATT&CK ids in D3FEND:", dnincount)
report_writer(
    "reports/attack_update-deprecated_attack_in_d3fend.txt", list(deprecated_in_d3)
)
