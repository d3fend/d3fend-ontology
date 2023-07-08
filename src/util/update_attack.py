from stix2 import MemoryStore, Filter
from rdflib import URIRef, Literal, RDF, RDFS, Namespace
from build import get_graph, _xmlns as _XMLNS
from pathlib import Path
import string
import sys


owl = Namespace('http://www.w3.org/2002/07/owl#')
rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
d3fend = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")

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
def get_stix_data(thesrc, graph):
    data = []
    query_results = thesrc.query([Filter('type', '=', 'attack-pattern')])
    superclasses_dict = generate_superclass(query_results)
    for tech in query_results:
        deprecated = tech.get("x_mitre_deprecated", False)
        revoked = tech.get("revoked", False)
        attack_id = next((ref.get("external_id") for ref in tech["external_references"] if ref.get("source_name") == "mitre-attack"), None)
        superclasses = superclasses_dict[attack_id]
        attack_uri = URIRef(_XMLNS + attack_id)
        current_label = graph.value(attack_uri, RDFS.label)
        label_change = False

        if (current_label != None):
            label_change = current_label.strip() != tech["name"]

        revoked_by_id = ""
        if revoked:
            revoked_by_dict = get_revoked_by(thesrc)
            revoked_by = revoked_by_dict[tech["id"]]
            revoked_by_tech = [obj for obj in query_results if obj.get("id") == revoked_by][0]
            revoked_by_id = next((ref.get("external_id") for ref in revoked_by_tech["external_references"] if ref.get("source_name") == "mitre-attack"), None)
        
        entry = {
            "data": tech,
            "id": attack_id,
            "superclasses": superclasses,
            "label": tech["name"], 
            "missing": current_label == None, 
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
    attack_id = next((ref.get("external_id") for ref in tech["external_references"] if ref.get("source_name") == "mitre-attack"), None)
    attack_uri = URIRef(_XMLNS + attack_id)
    new = 0

    if (None, None, Literal(attack_id)) in graph:
        deprecated_property = graph.value(attack_uri, owl.deprecated)
        # Check if tech already has deprecated annotations
        if deprecated_property is None:
            new = 1
            # Add a triple indicating deprecation
            graph.add((attack_uri, owl.deprecated, Literal(True)))
            graph.add((attack_uri, rdfs.comment, Literal(tech["description"].split("\n")[0])))
    return new

# Adds revoked annotations to techniques in d3fend graph
def add_revoked(graph, tech):
    revoked_by = tech["revoked_by"]
    tech = tech["data"]
    attack_id = next((ref.get("external_id") for ref in tech["external_references"] if ref.get("source_name") == "mitre-attack"), None)
    attack_uri = URIRef(_XMLNS + attack_id)
    new = 0

    if (None, None, Literal(attack_id)) in graph:
        revoked_property = graph.value(attack_uri, owl.deprecated)
        # Check if tech already has revoked annotations
        if revoked_property is None:
            new = 1
            # Add a triple indicating deprecation
            graph.add((attack_uri, rdfs.seeAlso, Literal(revoked_by)))
            graph.add((attack_uri, owl.deprecated, Literal(True)))
            graph.add((attack_uri, rdfs.comment, Literal(f"This technique has been revoked by {revoked_by}")))
    return new

# Returns a dictionary of which technique was revoked by another technique 
# Parses relationship objects in enterprise-attack.json
def get_revoked_by(thesrc):
    revoked_by = {}
    relationships = thesrc.query([
        Filter('type', '=', 'relationship'),
        Filter('relationship_type', '=', 'revoked-by'),
    ])
    for relationship in relationships:
        revoked_by[relationship.source_ref] = relationship.target_ref
    
    return revoked_by

# Returns a dictionary of superclasses for each technique
# If subtechnique, superclass is just parent technique
# If technique, superclass is tactic or list of tactics
def generate_superclass(all_techniques):
    superclass = {}
    for tech in all_techniques:
        attack_id = next((ref.get("external_id") for ref in tech["external_references"] if ref.get("source_name") == "mitre-attack"), None)
        if tech["x_mitre_is_subtechnique"]:
            superclass[attack_id] = attack_id.split(".")[0]
        else:
            classes = []
            for obj in tech["kill_chain_phases"]:
                name = str(string.capwords(obj["phase_name"].replace("-", " ")) + " Technique").replace(" ", "")
                classes.append(name)
            superclass[attack_id] = classes

    return superclass

# Adds missing techniques to ttl file 
def add_to_ttl(tech, graph):
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

    if tech["deprecated"]:
        graph.add((attack_uri, RDF.type, owl.Class))
        graph.add((attack_uri, RDFS.label, Literal(name)))
        if subtechnique:
            graph.add((attack_uri, RDFS.subClassOf, d3fend[subclass]))
        else:
            # Handle multiple superclasses 
            for subclass_of in subclass:
                graph.add((attack_uri, RDFS.subClassOf, d3fend[subclass_of]))
        graph.add((attack_uri, d3fend['attack-id'], Literal(attack_id)))
        graph.add((attack_uri, owl.deprecated, Literal(True)))
        graph.add((attack_uri, rdfs.comment, Literal(tech["data"]["description"].split("\n")[0])))
        key = "missing_deprecated"

    elif tech["revoked"]:
        graph.add((attack_uri, RDF.type, owl.Class))
        graph.add((attack_uri, RDFS.label, Literal(name)))
        if subtechnique:
            graph.add((attack_uri, RDFS.subClassOf, d3fend[subclass]))
        else:
            for subclass_of in subclass:
                graph.add((attack_uri, RDFS.subClassOf, d3fend[subclass_of]))
        graph.add((attack_uri, d3fend['attack-id'], Literal(attack_id)))
        graph.add((attack_uri, owl.deprecated, Literal(True)))
        graph.add((attack_uri, rdfs.seeAlso, Literal(revoked_by)))
        graph.add((attack_uri, rdfs.comment, Literal(f"This technique has been revoked by {revoked_by}")))
        key = "missing_revoked"

    else:
        graph.add((attack_uri, RDF.type, owl.Class))
        graph.add((attack_uri, RDFS.label, Literal(name)))
        if subtechnique:
            graph.add((attack_uri, RDFS.subClassOf, d3fend[subclass]))
        else:
            for subclass_of in subclass:
                graph.add((attack_uri, RDFS.subClassOf, d3fend[subclass_of]))
        graph.add((attack_uri, d3fend['attack-id'], Literal(attack_id)))
        key = "missing_neither"
    return key

def update_and_add(graph, data):
    # If tech is missing, add it to d3fend-protege.updates.ttl
    # Else, handle if technique has recently become deprecated, revoked, or has an updated label

    counters = {
        "missing": 0, 
        "missing_deprecated": 0, 
        "missing_revoked": 0,
        "missing_neither": 0,
        "recently_deprecated": 0, 
        "recently_revoked": 0,
        "label_change": 0
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
                attack_uri = URIRef(_XMLNS + tech["id"])
                current_label = graph.value(attack_uri, RDFS.label)
                graph.remove((attack_uri, RDFS.label, current_label))
                graph.add((attack_uri, RDFS.label, Literal(tech["label"])))
                counters["label_change"] += 1
    
    return counters


def main(do_counters=True, ATTACK_VERSION="13.1"):

    src = MemoryStore()
    src.load_from_file(f"data/enterprise-attack-{ATTACK_VERSION}.json")
    d3fend_graph = get_graph(filename="src/ontology/d3fend-protege.updates.ttl")
    
    data = get_stix_data(src, d3fend_graph) # parse stix data
    counters = update_and_add(d3fend_graph, data) # add new techniques and modify current ones 

    d3fend_graph.serialize(destination="src/ontology/d3fend-protege.updates.ttl", format="turtle")

    if do_counters:
        # Print some stats 
        _print("Valid ATT&CK ids found in stix document:", len(data))
        _print("Valid ATT&CK ids missing from D3FEND graph:", counters["missing"])
        _print("Valid Deprecated ATT&CK ids missing from D3FEND graph:", counters["missing_deprecated"])
        _print("Valid Revoked ATT&CK ids missing from D3FEND graph:", counters["missing_revoked"])
        _print("Recently Deprecated ATT&CK ids in D3FEND graph:", counters["recently_deprecated"])
        _print("Recently Revoked ATT&CK ids in D3FEND graph:", counters["recently_revoked"])
        _print("Valid ATT&CK ids in graph that needed label change in graph:", counters["label_change"])

if __name__ == "__main__":
    version = sys.argv[1]
    main(do_counters=True, ATTACK_VERSION=version)