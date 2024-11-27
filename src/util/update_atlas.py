from stix2 import MemoryStore, Filter
from rdflib import URIRef, Literal, RDF, RDFS, Namespace, BNode, SKOS
from build import get_graph, _xmlns as _XMLNS
import string
import sys

owl = Namespace("http://www.w3.org/2002/07/owl#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
d3fend = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")


def _print(*args):
    print(" ".join([str(a) for a in args]).rjust(80, " "))
    print()


# Parses data in stix-atlas.json and returns list of techniques with following annotations:
#   id: atlas id
#   superclasses: superclass, list of superclasses if not subtechnique
#   label: technique name
#   missing: is tech missing from d3fend graph
#   label_change: does tech's label need updating
#   deprecated: if tech is deprecated
#   revoked: if tech is revoked
#   revoked_by: tech revoked technique is revoked by
def get_stix_data(thesrc, graph):
    data = []
    query_results = thesrc.query(
        [
            Filter("external_references.source_name", "=", "mitre-atlas"),
            Filter("type", "=", "attack-pattern"),
        ]
    )
    superclasses_dict = generate_superclass(query_results, thesrc)
    for tech in query_results:
        deprecated = tech.get("x_mitre_deprecated", False)
        revoked = tech.get("revoked", False)
        atlas_id = next(
            (
                ref.get("external_id")
                for ref in tech["external_references"]
                if ref.get("source_name") == "mitre-atlas"
            ),
            None,
        )
        superclasses = superclasses_dict[atlas_id]
        atlas_uri = URIRef(_XMLNS + atlas_id)
        current_label = graph.value(atlas_uri, RDFS.label)
        label_change = False

        if current_label is not None:
            label_change = current_label.strip() != tech["name"]

        revoked_by_id = ""
        if revoked:
            revoked_by_dict = get_revoked_by(thesrc)
            revoked_by = revoked_by_dict[tech["id"]]
            revoked_by_tech = [
                obj for obj in query_results if obj.get("id") == revoked_by
            ][0]
            revoked_by_id = next(
                (
                    ref.get("external_id")
                    for ref in revoked_by_tech["external_references"]
                    if ref.get("source_name") == "mitre-atlas"
                ),
                None,
            )

        entry = {
            "data": tech,
            "id": atlas_id,
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
def add_deprecated(graph, tech):
    tech = tech["data"]
    atlas_id = next(
        (
            ref.get("external_id")
            for ref in tech["external_references"]
            if ref.get("source_name") == "mitre-atlas"
        ),
        None,
    )
    atlas_uri = URIRef(_XMLNS + atlas_id)
    new = 0

    if (None, None, Literal(atlas_id)) in graph:
        deprecated_property = graph.value(atlas_uri, owl.deprecated)
        # Check if tech already has deprecated annotations
        if deprecated_property is None:
            new = 1
            # Add a triple indicating deprecation
            graph.add((atlas_uri, owl.deprecated, Literal(True)))
            graph.add(
                (atlas_uri, rdfs.comment, Literal(tech["description"].split("\n")[0]))
            )
    return new


# Adds revoked annotations to techniques in d3fend graph
def add_revoked(graph, tech):
    revoked_by = tech["revoked_by"]
    tech = tech["data"]
    atlas_id = next(
        (
            ref.get("external_id")
            for ref in tech["external_references"]
            if ref.get("source_name") == "mitre-atlas"
        ),
        None,
    )
    atlas_uri = URIRef(_XMLNS + atlas_id)
    new = 0

    if (None, None, Literal(atlas_id)) in graph:
        revoked_property = graph.value(atlas_uri, owl.deprecated)
        # Check if tech already has revoked annotations
        if revoked_property is None:
            new = 1
            # Add a triple indicating deprecation
            graph.add((atlas_uri, rdfs.seeAlso, Literal(revoked_by)))
            graph.add((atlas_uri, owl.deprecated, Literal(True)))
            graph.add(
                (
                    atlas_uri,
                    rdfs.comment,
                    Literal(f"This technique has been revoked by {revoked_by}"),
                )
            )
    return new


# Returns a dictionary of which technique was revoked by another technique
# Parses relationship objects in stix-atlas.json
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
def generate_superclass(all_techniques, thesrc):
    superclass = {}

    # Query to retrieve all tactics from the source
    tactics = thesrc.query(
        [
            Filter("external_references.source_name", "=", "mitre-atlas"),
            Filter("type", "=", "x-mitre-tactic"),
        ]
    )

    # Create a dictionary to map tactic short names to their IDs
    tactic_dict = {}
    for tactic in tactics:
        # Assume each tactic has one or more external_references and has a property x_mitre_shortname
        shortname = tactic["x_mitre_shortname"]
        for ref in tactic["external_references"]:
            if ref.get("source_name") == "mitre-atlas":
                tactic_dict[shortname] = {
                    "data": tactic,
                    "name": ref.get("external_id"),
                }

    for tech in all_techniques:
        atlas_id = next(
            (
                ref.get("external_id")
                for ref in tech["external_references"]
                if ref.get("source_name") == "mitre-atlas"
            ),
            None,
        )
        if atlas_id:
            # Check if it is a subtechnique
            if tech.get("x_mitre_is_subtechnique", False):
                # Parent technique's ID is part of the atlas_id for subtechniques
                superclass[atlas_id] = (
                    atlas_id.split(".")[0] + "." + atlas_id.split(".")[1]
                )
            else:
                # List to hold all superclasses for this technique
                classes = []
                # Iterate over kill chain phases
                for obj in tech["kill_chain_phases"]:
                    name = str(
                        "ATLAS "
                        + string.capwords(obj["phase_name"].replace("-", " "))
                        + " Technique"
                    ).replace(" ", "")
                    fixed_name = name.replace("ATLASMl", "ATLASML")
                    classes.append(fixed_name)
                    superclass[atlas_id] = classes

    return superclass


# Adds missing techniques to ttl file
def add_to_ttl(tech, graph):
    # 3 cases:
    # Not deprecated or revoked: add class, label, atlas-id, subClassOf
    # Deprecated: add class, label, atlas-id, subclassOf, owl:deprecated true
    # Revoked: add class, label, atlas-id, subClassOf, owl:deprecated true, rdfs:seeAlso revoked_by_technique
    # Have not seen any cases of deprecated & revoked

    name = tech["label"]
    atlas_id = tech["id"]
    subclass = tech["superclasses"]
    revoked_by = tech["revoked_by"]
    subtechnique = tech["data"].get("x_mitre_is_subtechnique", False)
    atlas_uri = URIRef(_XMLNS + atlas_id)
    key = ""

    if tech["deprecated"]:
        graph.add((atlas_uri, RDF.type, owl.Class))
        graph.add((atlas_uri, RDFS.label, Literal(name)))
        if subtechnique:
            graph.add((atlas_uri, RDFS.subClassOf, d3fend[subclass]))
        else:
            # Handle multiple superclasses
            for subclass_of in subclass:
                graph.add((atlas_uri, RDFS.subClassOf, d3fend[subclass_of]))
        graph.add((atlas_uri, d3fend["atlas-id"], Literal(atlas_id)))
        graph.add((atlas_uri, owl.deprecated, Literal(True)))
        graph.add(
            (
                atlas_uri,
                rdfs.comment,
                Literal(tech["data"]["description"].split("\n")[0]),
            )
        )
        key = "missing_deprecated"

    elif tech["revoked"]:
        graph.add((atlas_uri, RDF.type, owl.Class))
        graph.add((atlas_uri, RDFS.label, Literal(name)))
        if subtechnique:
            graph.add((atlas_uri, RDFS.subClassOf, d3fend[subclass]))
        else:
            for subclass_of in subclass:
                graph.add((atlas_uri, RDFS.subClassOf, d3fend[subclass_of]))
        graph.add((atlas_uri, d3fend["atlas-id"], Literal(atlas_id)))
        graph.add((atlas_uri, owl.deprecated, Literal(True)))
        graph.add((atlas_uri, rdfs.seeAlso, Literal(revoked_by)))
        graph.add(
            (
                atlas_uri,
                rdfs.comment,
                Literal(f"This technique has been revoked by {revoked_by}"),
            )
        )
        key = "missing_revoked"

    else:
        graph.add((atlas_uri, RDF.type, owl.Class))
        graph.add((atlas_uri, RDF.type, owl.NamedIndividual))
        graph.add((atlas_uri, RDF.type, d3fend["ATLASTechnique"]))
        graph.add((atlas_uri, RDFS.label, Literal(name)))
        graph.add(
            (
                atlas_uri,
                RDFS.seeAlso,
                URIRef("https://atlas.mitre.org/techniques/" + atlas_id),
            )
        )
        if subtechnique:
            graph.add((atlas_uri, RDFS.subClassOf, d3fend[subclass]))
        else:
            for subclass_of in subclass:
                graph.add((atlas_uri, RDFS.subClassOf, d3fend[subclass_of]))
        graph.add((atlas_uri, d3fend["atlas-id"], Literal(atlas_id)))
        key = "missing_neither"
    return key


def update_definition(graph, tech):
    tech = tech["data"]
    atlas_id = next(
        (
            ref.get("external_id")
            for ref in tech["external_references"]
            if ref.get("source_name") == "mitre-atlas"
        ),
        None,
    )
    atlas_uri = URIRef(_XMLNS + atlas_id)
    new = 0

    if (None, None, Literal(atlas_id)) in graph:

        def_property = graph.value(atlas_uri, d3fend["definition"])
        # Check if tech already has definition
        if def_property is None:
            new = 1
            # Add definition
            graph.add(
                (
                    atlas_uri,
                    d3fend["definition"],
                    Literal(tech["description"].split("\n")[0]),
                )
            )
    return new


def update_and_add(graph, data, thesrc):
    # If tech is missing, add it to d3fend-protege.atlas.ttl
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
            key = add_to_ttl(tech, graph)
            counters["missing"] += 1
            counters[key] += 1
        else:
            if tech["deprecated"]:
                new = add_deprecated(graph, tech)
                counters["recently_deprecated"] += new
            elif tech["revoked"]:
                new = add_revoked(graph, tech)
                counters["recently_revoked"] += new
            elif tech["label_change"]:
                atlas_uri = URIRef(_XMLNS + tech["id"])
                current_label = graph.value(atlas_uri, RDFS.label)
                graph.remove((atlas_uri, RDFS.label, current_label))
                graph.add((atlas_uri, RDFS.label, Literal(tech["label"])))
                counters["label_change"] += 1
        update_definition(graph, tech)

    # Add tactics to graph
    for tactic in thesrc.query(
        [
            Filter("external_references.source_name", "=", "mitre-atlas"),
            Filter("type", "=", "x-mitre-tactic"),
        ]
    ):
        atlas_id = next(
            (
                ref.get("external_id")
                for ref in tactic["external_references"]
                if ref.get("source_name") == "mitre-atlas"
            ),
            None,
        )
        tactic_uri = URIRef(_XMLNS + atlas_id)
        if (tactic_uri, None, None) not in graph:
            graph.add((tactic_uri, RDF.type, owl.Class))
            graph.add((tactic_uri, RDF.type, owl.NamedIndividual))
            graph.add((tactic_uri, RDF.type, d3fend["ATLASTactic"]))
            graph.add((tactic_uri, RDFS.label, Literal(tactic["name"] + " - ATLAS")))
            graph.add((tactic_uri, SKOS.prefLabel, Literal(tactic["name"])))
            graph.add((tactic_uri, RDFS.subClassOf, d3fend["ATLASTactic"]))
            graph.add((tactic_uri, RDFS.subClassOf, d3fend["OffensiveTactic"]))
            graph.add(
                (
                    tactic_uri,
                    d3fend["definition"],
                    Literal(tactic["description"].split("\n")[0]),
                )
            )
            graph.add((tactic_uri, d3fend["atlas-id"], Literal(atlas_id)))
            graph.add(
                (
                    tactic_uri,
                    RDFS.seeAlso,
                    URIRef("https://atlas.mitre.org/tactics/" + atlas_id),
                )
            )
        tech_name = str("ATLAS" + tactic["name"] + " Technique").replace(" ", "")
        tactic_technique_uri = URIRef(_XMLNS + tech_name)
        if (tactic_technique_uri, None, None) not in graph:
            graph.add((tactic_technique_uri, RDF.type, owl.Class))
            graph.add(
                (
                    tactic_technique_uri,
                    RDFS.label,
                    Literal(tactic["name"] + " - ATLAS - Technique"),
                )
            )
            graph.add((tactic_technique_uri, RDFS.subClassOf, d3fend["ATLASTechnique"]))
            graph.add(
                (tactic_technique_uri, RDFS.subClassOf, d3fend["OffensiveTechnique"])
            )
            enables = BNode()
            graph.add((enables, RDF.type, owl.Restriction))
            graph.add((enables, owl.onProperty, d3fend["enables"]))
            graph.add((enables, owl.someValuesFrom, d3fend[atlas_id]))
            graph.add((tactic_technique_uri, RDFS.subClassOf, enables))

    # Add mitigations to graph
    for mitigation in thesrc.query(
        [
            Filter("external_references.source_name", "=", "mitre-atlas"),
            Filter("type", "=", "course-of-action"),
        ]
    ):
        atlas_id = next(
            (
                ref.get("external_id")
                for ref in mitigation["external_references"]
                if ref.get("source_name") == "mitre-atlas"
            ),
            None,
        )
        mitigation_uri = URIRef(_XMLNS + atlas_id)

        relations = thesrc.relationships(
            mitigation["id"], "mitigates", source_only=True
        )
        mitigates_techs = [
            tech
            for tech in thesrc.query(
                [Filter("id", "in", [rel.target_ref for rel in relations])]
            )
        ]
        mitigates = [
            next(
                (
                    ref.get("external_id")
                    for ref in tech["external_references"]
                    if ref.get("source_name") == "mitre-atlas"
                ),
                None,
            )
            for tech in mitigates_techs
        ]

        if (mitigation_uri, None, None) not in graph:
            graph.add((mitigation_uri, RDF.type, owl.NamedIndividual))
            graph.add((mitigation_uri, RDF.type, d3fend["ATLASMitigation"]))
            graph.add((mitigation_uri, RDFS.label, Literal(mitigation["name"])))
            graph.add(
                (
                    mitigation_uri,
                    d3fend["definition"],
                    Literal(mitigation["description"].split("\n")[0]),
                )
            )
            graph.add((mitigation_uri, d3fend["atlas-id"], Literal(atlas_id)))
            graph.add(
                (
                    mitigation_uri,
                    RDFS.seeAlso,
                    URIRef("https://atlas.mitre.org/mitigations/" + atlas_id),
                )
            )

            for tech_atlas_id in mitigates:
                graph.add((mitigation_uri, d3fend["related"], d3fend[tech_atlas_id]))

    return counters


def main(do_counters=True, ATLAS_VERSION="4.6.0"):

    src = MemoryStore()
    src.load_from_file("data/stix-atlas.json")
    d3fend_graph = get_graph(filename="src/ontology/d3fend-protege.atlas.ttl")

    data = get_stix_data(src, d3fend_graph)  # parse stix data
    counters = update_and_add(
        d3fend_graph, data, src
    )  # add new techniques and modify current ones

    d3fend_graph.serialize(
        destination="src/ontology/d3fend-protege.atlas.ttl", format="turtle"
    )

    if do_counters:
        # Print some stats
        _print("Valid ATLAS ids found in stix document:", len(data))
        _print("Valid ATLAS ids missing from D3FEND graph:", counters["missing"])
        _print(
            "Valid Deprecated ATLAS ids missing from D3FEND graph:",
            counters["missing_deprecated"],
        )
        _print(
            "Valid Revoked ATLAS ids missing from D3FEND graph:",
            counters["missing_revoked"],
        )
        _print(
            "Recently Deprecated ATLAS ids in D3FEND graph:",
            counters["recently_deprecated"],
        )
        _print(
            "Recently Revoked ATLAS ids in D3FEND graph:", counters["recently_revoked"]
        )
        _print(
            "Valid ATLAS ids in graph that needed label change in graph:",
            counters["label_change"],
        )


if __name__ == "__main__":
    version = sys.argv[1]
    main(do_counters=True, ATLAS_VERSION=version)
