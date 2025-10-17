import argparse
import string

from rdflib import URIRef, Literal, RDF, RDFS, Namespace
from stix2 import MemoryStore, Filter

from build import get_graph, _xmlns as _XMLNS


owl = Namespace("http://www.w3.org/2002/07/owl#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
d3fend = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")
skos = Namespace("http://www.w3.org/2004/02/skos/core#")

SUPPORTED_FRAMEWORKS = {"enterprise", "ics", "mobile"}


def get_framework_labels(original_label, framework):
    """
    Given a technique's original label (original_label) and a framework,
    return a tuple (new_label, pref_label) where:
      • new_label is the label to store as rdfs:label. For "ics" and "mobile"
        a suffix is appended (e.g., " - ATTACK ICS" or " - ATTACK Mobile").
      • pref_label is the preferred label (to be stored as skos:prefLabel) or
        None if no separate preferred label is needed.
    For enterprise, no changes are made.
    """
    fw = framework.lower()
    if fw == "enterprise":
        return original_label, None
    elif fw == "ics":
        return original_label + " - ATTACK ICS", original_label
    elif fw == "mobile":
        return original_label + " - ATTACK Mobile", original_label
    else:
        return original_label, None


def _print(*args):
    print(" ".join([str(a) for a in args]).rjust(80, " "))
    print()


# Parses data in enterprise-attack.json and returns list of techniques with following annotations:
#   id: attack id
#   superclasses: superclass, list of superclasses if not subtechnique
#   label: technique name
#   missing: is tech missing from d3fend graph
#   label_change: does tech's label need updating
#   deprecated: if tech is deprecated
#   revoked: if tech is revoked
#   revoked_by: tech revoked technique is revoked by
def get_stix_data(thesrc, graph, framework="enterprise"):
    data = []
    query_results = thesrc.query(
        [
            Filter("type", "=", "attack-pattern"),
            Filter(
                "kill_chain_phases.kill_chain_name",
                "=",
                "mitre-attack"
                if framework == "enterprise"
                else f"mitre-{framework}-attack",
            ),
            Filter(
                "kill_chain_phases.phase_name",
                "!=",
                "network-effects",
            ),
            Filter(
                "kill_chain_phases.phase_name",
                "!=",
                "remote-service-effects",
            ),
        ]
    )
    superclasses_dict = generate_superclass(query_results, framework)
    revoked_by_dict = get_revoked_by(thesrc)
    for tech in query_results:
        deprecated = tech.get("x_mitre_deprecated", False)
        revoked = tech.get("revoked", False)
        attack_id = next(
            (
                ref.get("external_id")
                for ref in tech["external_references"]
                if ref.get("source_name") == "mitre-attack"
                or ref.get("source_name") == f"mitre-{framework}-attack"
            ),
            None,
        )
        superclasses = superclasses_dict[attack_id]
        attack_uri = URIRef(_XMLNS + attack_id)
        current_label = graph.value(attack_uri, RDFS.label)
        label_change = False

        if current_label is not None:
            label_change = current_label.strip() != tech["name"]

        revoked_by_id = ""
        if revoked:
            revoked_by = revoked_by_dict.get(tech["id"])
            revoked_by_tech = None
            if revoked_by is not None:
                # Attempt to fetch the revoking technique from the store; fall back to cached query
                revoked_by_tech = thesrc.get(revoked_by)
                if revoked_by_tech is None:
                    revoked_by_tech = next(
                        (obj for obj in query_results if obj.get("id") == revoked_by),
                        None,
                    )

            if revoked_by_tech is not None:
                revoked_by_id = next(
                    (
                        ref.get("external_id")
                        for ref in revoked_by_tech["external_references"]
                        if ref.get("source_name") == "mitre-attack"
                    ),
                    None,
                )

        entry = {
            "data": tech,
            "id": attack_id,
            "superclasses": superclasses,
            "label": tech["name"],
            "missing": current_label is None,
            "label_change": label_change,
            "deprecated": deprecated,
            "revoked": revoked,
            "revoked_by": revoked_by_id,
        }
        data.append(entry)

    return data


# Adds deprecated annotations to techniques in d3fend graph
def add_deprecated(graph, tech_entry, framework):
    attack_id = tech_entry.get("id")
    if attack_id is None:
        return 0

    attack_uri = URIRef(_XMLNS + attack_id)
    new = 0

    if (None, None, Literal(attack_id)) in graph:
        deprecated_property = graph.value(attack_uri, owl.deprecated)
        # Check if tech already has deprecated annotations
        if deprecated_property is None:
            new = 1
            # Add a triple indicating deprecation
            graph.add((attack_uri, owl.deprecated, Literal(True)))
            comment_text = get_deprecated_comment(tech_entry, framework)
            if comment_text:
                graph.add((attack_uri, rdfs.comment, Literal(comment_text)))
    return new


# Adds revoked annotations to techniques in d3fend graph
def add_revoked(graph, tech_entry):
    revoked_by = tech_entry.get("revoked_by")
    attack_id = tech_entry.get("id")
    if attack_id is None:
        return 0

    attack_uri = URIRef(_XMLNS + attack_id)
    new = 0

    if (None, None, Literal(attack_id)) in graph:
        revoked_property = graph.value(attack_uri, owl.deprecated)
        # Check if tech already has revoked annotations
        if revoked_property is None:
            new = 1
            # Add a triple indicating deprecation
            if revoked_by:
                graph.add((attack_uri, rdfs.seeAlso, d3fend[revoked_by]))
            graph.add((attack_uri, owl.deprecated, Literal(True)))
            graph.add(
                (
                    attack_uri,
                    rdfs.comment,
                    Literal(f"This technique has been revoked by {revoked_by}"),
                )
            )
    return new


# Returns a dictionary of which technique was revoked by another technique
# Parses relationship objects in enterprise-attack.json
def get_revoked_by(thesrc):
    revoked_by = {}
    relationships = thesrc.query(
        [
            Filter("type", "=", "relationship"),
            Filter("relationship_type", "=", "revoked-by"),
        ]
    )
    for relationship in relationships:
        revoked_by[relationship.source_ref] = relationship.target_ref

    return revoked_by


# Returns a dictionary of superclasses for each technique
# If subtechnique, superclass is just parent technique
# If technique, superclass is tactic or list of tactics
def generate_superclass(all_techniques, framework):
    superclass = {}
    for tech in all_techniques:
        attack_id = next(
            (
                ref.get("external_id")
                for ref in tech["external_references"]
                if ref.get("source_name") == "mitre-attack"
                or ref.get("source_name") == f"mitre-{framework}-attack"
            ),
            None,
        )
        if tech["x_mitre_is_subtechnique"]:
            superclass[attack_id] = attack_id.split(".")[0]
        else:
            classes = []
            for obj in tech["kill_chain_phases"]:
                phase_name = string.capwords(obj["phase_name"].replace("-", " "))
                class_base = phase_name.replace(" ", "") + "Technique"
                if framework == "enterprise":
                    name = class_base
                else:
                    prefix = "ATTACK" + (
                        framework.upper()
                        if framework == "ics"
                        else framework.capitalize()
                    )
                    name = prefix + class_base
                classes.append(name)
            superclass[attack_id] = classes

    return superclass


# Adds missing techniques to ttl file
def add_to_ttl(tech, graph, framework="enterprise"):
    # 3 cases:
    # Not deprecated or revoked: add class, label, attack-id, subClassOf
    # Deprecated: add class, label, attack-id, subclassOf, owl:deprecated true
    # Revoked: add class, label, attack-id, subClassOf, owl:deprecated true, rdfs:seeAlso revoked_by_technique
    # Have not seen any cases of deprecated & revoked

    name = tech["label"]
    attack_id = tech["id"]
    subclass = tech["superclasses"]
    revoked_by = tech["revoked_by"]
    subtechnique = tech["data"]["x_mitre_is_subtechnique"]
    attack_uri = URIRef(_XMLNS + attack_id)
    key = ""
    mod_label, pref_label = get_framework_labels(name, framework)

    if pref_label is not None:
        graph.add((attack_uri, skos.prefLabel, Literal(pref_label)))

    ensure_superclasses(graph, attack_uri, subclass, framework, subtechnique)

    if tech["deprecated"]:
        graph.add((attack_uri, RDF.type, owl.Class))
        graph.add((attack_uri, RDFS.label, Literal(mod_label)))
        graph.add((attack_uri, d3fend["attack-id"], Literal(attack_id)))
        graph.add((attack_uri, owl.deprecated, Literal(True)))
        comment_text = get_deprecated_comment(tech, framework)
        if comment_text:
            graph.add((attack_uri, rdfs.comment, Literal(comment_text)))
        key = "missing_deprecated"

    elif tech["revoked"]:
        graph.add((attack_uri, RDF.type, owl.Class))
        graph.add((attack_uri, RDFS.label, Literal(mod_label)))
        graph.add((attack_uri, d3fend["attack-id"], Literal(attack_id)))
        graph.add((attack_uri, owl.deprecated, Literal(True)))
        graph.add((attack_uri, rdfs.seeAlso, d3fend[revoked_by]))
        graph.add(
            (
                attack_uri,
                rdfs.comment,
                Literal(f"This technique has been revoked by {revoked_by}"),
            )
        )
        key = "missing_revoked"

    else:
        graph.add((attack_uri, RDF.type, owl.Class))
        graph.add((attack_uri, RDFS.label, Literal(mod_label)))
        graph.add((attack_uri, d3fend["attack-id"], Literal(attack_id)))
        key = "missing_neither"
    return key


def update_definition(graph, tech, framework):
    tech = tech["data"]
    attack_id = next(
        (
            ref.get("external_id")
            for ref in tech["external_references"]
            if ref.get("source_name") == "mitre-attack"
            or ref.get("source_name") == f"mitre-{framework}-attack"
        ),
        None,
    )
    attack_uri = URIRef(_XMLNS + attack_id)
    new = 0

    if (None, None, Literal(attack_id)) in graph:

        def_property = graph.value(attack_uri, d3fend["definition"])
        # Check if tech already has definition
        if def_property is None:
            new = 1
            # Add definition
            graph.add(
                (
                    attack_uri,
                    d3fend["definition"],
                    Literal(tech["description"].strip().split("\n")[0].strip()),
                )
            )
    return new


def get_deprecated_comment(tech_entry, _framework):
    revoked_by = tech_entry.get("revoked_by")
    if revoked_by:
        return f"This technique has been revoked by {revoked_by}"

    description = tech_entry["data"].get("description", "")
    first_line = description.strip().split("\n")[0].strip()
    if first_line and "deprecated" in first_line.lower():
        return first_line

    return "This technique has been deprecated."


def ensure_superclasses(graph, attack_uri, subclass, framework, subtechnique):
    desired = set()

    if subtechnique:
        target = d3fend[subclass]
        desired.add(target)
    else:
        for subclass_of in subclass:
            desired.add(d3fend[subclass_of])

    for target in desired:
        if (attack_uri, RDFS.subClassOf, target) not in graph:
            graph.add((attack_uri, RDFS.subClassOf, target))

    if framework == "enterprise":
        prefix = _XMLNS + "ATTACKEnterprise"
        for obj in list(graph.objects(attack_uri, RDFS.subClassOf)):
            if (
                isinstance(obj, URIRef)
                and str(obj).startswith(prefix)
                and obj not in desired
            ):
                graph.remove((attack_uri, RDFS.subClassOf, obj))


def update_and_add(graph, data, framework="enterprise"):
    # If tech is missing, add it to d3fend-protege.updates.ttl
    # Else, handle if technique has recently become deprecated, revoked, or has an updated label

    counters = {
        "missing": 0,
        "missing_deprecated": 0,
        "missing_revoked": 0,
        "missing_neither": 0,
        "recently_deprecated": 0,
        "recently_revoked": 0,
        "label_change": 0,
    }

    for tech in data:
        if tech["missing"]:
            key = add_to_ttl(tech, graph, framework)
            counters["missing"] += 1
            counters[key] += 1
        else:
            attack_uri = URIRef(_XMLNS + tech["id"])
            ensure_superclasses(
                graph,
                attack_uri,
                tech["superclasses"],
                framework,
                tech["data"]["x_mitre_is_subtechnique"],
            )
            if tech["deprecated"]:
                new = add_deprecated(graph, tech, framework)
                counters["recently_deprecated"] += new
            elif tech["revoked"]:
                new = add_revoked(graph, tech)
                counters["recently_revoked"] += new
            elif tech["label_change"]:
                current_label = graph.value(attack_uri, RDFS.label)
                graph.remove((attack_uri, RDFS.label, current_label))
                mod_label, pref_label = get_framework_labels(tech["label"], framework)
                graph.add((attack_uri, RDFS.label, Literal(mod_label)))
                if pref_label is not None:
                    graph.add((attack_uri, skos.prefLabel, Literal(pref_label)))
                counters["label_change"] += 1
        update_definition(graph, tech, framework)

    return counters


def main(attack_version, frameworks=None, do_counters=True):

    if frameworks is None:
        frameworks = ["enterprise"]

    # Load the base D3FEND graph
    d3fend_graph = get_graph(filename="src/ontology/d3fend-protege.updates.ttl")

    # Initialize cumulative counters
    total_counters = {
        "missing": 0,
        "missing_deprecated": 0,
        "missing_revoked": 0,
        "missing_neither": 0,
        "recently_deprecated": 0,
        "recently_revoked": 0,
        "label_change": 0,
    }

    framework_results = []
    for framework in frameworks:
        stix_file = f"data/{framework}-attack-{attack_version}.json"
        print(f"\nProcessing {framework} STIX file: {stix_file}")
        src = MemoryStore()
        src.load_from_file(stix_file)
        data = get_stix_data(src, d3fend_graph, framework)
        counters = update_and_add(d3fend_graph, data, framework)
        for key in total_counters:
            total_counters[key] += counters.get(key, 0)
        framework_results.append((framework, counters, len(data)))

    # Serialize the updated graph
    d3fend_graph.serialize(
        destination="src/ontology/d3fend-protege.updates.ttl", format="turtle"
    )

    if do_counters:
        # Print per-framework stats
        for framework, counters, count in framework_results:
            _print(f"[{framework}] Valid ATT&CK ids found in stix document: ", count)
            _print(
                f"[{framework}] Valid ATT&CK ids missing from D3FEND graph: ",
                counters["missing"],
            )
            _print(
                f"[{framework}] Valid Deprecated ATT&CK ids missing from D3FEND graph: ",
                counters["missing_deprecated"],
            )
            _print(
                f"[{framework}] Valid Revoked ATT&CK ids missing from D3FEND graph: ",
                counters["missing_revoked"],
            )
            _print(
                f"[{framework}] Recently Deprecated ATT&CK ids in D3FEND graph: ",
                counters["recently_deprecated"],
            )
            _print(
                f"[{framework}] Recently Revoked ATT&CK ids in D3FEND graph: ",
                counters["recently_revoked"],
            )
            _print(
                f"[{framework}] Valid ATT&CK ids in graph that needed label change in graph: ",
                counters["label_change"],
            )
        if len(frameworks) > 1:
            _print(
                "Total Valid ATT&CK ids missing from D3FEND graph: ",
                total_counters["missing"],
            )
            _print(
                "Total Valid Deprecated ATT&CK ids missing from D3FEND graph: ",
                total_counters["missing_deprecated"],
            )
            _print(
                "Total Valid Revoked ATT&CK ids missing from D3FEND graph: ",
                total_counters["missing_revoked"],
            )
            _print(
                "Total Recently Deprecated ATT&CK ids in D3FEND graph: ",
                total_counters["recently_deprecated"],
            )
            _print(
                "Total Recently Revoked ATT&CK ids in D3FEND graph: ",
                total_counters["recently_revoked"],
            )
            _print(
                "Total Valid ATT&CK ids in graph that needed label change in graph: ",
                total_counters["label_change"],
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Update D3FEND ontology with ATT&CK techniques from the specified frameworks."
        )
    )
    parser.add_argument(
        "version",
        help="ATT&CK data version to process (e.g., 17.1).",
    )
    parser.add_argument(
        "frameworks",
        nargs="*",
        help="Frameworks to include: enterprise, ics, mobile. Defaults to enterprise.",
    )
    args = parser.parse_args()

    frameworks = args.frameworks or ["enterprise" "ics" "mobile"]
    invalid = sorted(set(frameworks) - SUPPORTED_FRAMEWORKS)
    if invalid:
        parser.error(
            f"Unsupported frameworks: {', '.join(invalid)}. "
            f"Supported values are: {', '.join(sorted(SUPPORTED_FRAMEWORKS))}."
        )

    main(attack_version=args.version, frameworks=frameworks, do_counters=True)
