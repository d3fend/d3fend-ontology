from update_attack import get_stix_data, update_and_add
from stix2 import MemoryStore, Filter
from rdflib import URIRef, Literal, Graph, RDF, RDFS, Namespace
from build import get_graph, _xmlns as _XMLNS

owl = Namespace('http://www.w3.org/2002/07/owl#')
rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
d3fend = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")

test_graph = """
    @prefix : <http://d3fend.mitre.org/ontologies/d3fend.owl#> .
    @prefix dcterms: <http://purl.org/dc/terms/> .
    @prefix owl: <http://www.w3.org/2002/07/owl#> .
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    :T1053.005 a owl:Class ;
        rdfs:label "Schtasks Execution" ;
        rdfs:subClassOf :T1053 ;
        :attack-id "T1053.005" ;
        :definition "Renamed from ATT&CK to be consistent with at, launchd, cron siblings; name as is looks like parent.  Not sure why parent is not just Scheduled Task [Execution[." .
    
    :T1047 a owl:Class ;
        rdfs:label "Windows Management Instrumentation Execution" ;
        rdfs:subClassOf :ExecutionTechnique,
            [ a owl:Restriction ;
                owl:onProperty :may-create ;
                owl:someValuesFrom :IntranetAdministrativeNetworkTraffic ],
            [ a owl:Restriction ;
                owl:onProperty :may-invoke ;
                owl:someValuesFrom :CreateProcess ] ;
        :attack-id "T1047" .

    :T1156 a owl:Class ;
        rdfs:label "Malicious Shell Modification" ;
        rdfs:subClassOf :PersistenceTechnique ;
        :attack-id "T1156" .
    
    :T1026 a owl:Class ;
        rdfs:label "Multiband Communication" ;
        rdfs:subClassOf :CommandAndControlTechnique ;
        :attack-id "T1026" .

    :T1546.004 a owl:Class ;
        rdfs:label ".bash_profile and .bashrc" ;
        rdfs:subClassOf :T1546,
            [ a owl:Restriction ;
                owl:onProperty :modifies ;
                owl:someValuesFrom :UserInitConfigurationFile ] ;
        :attack-id "T1546.004" .
    
    :T1027.005 a owl:Class ;
        rdfs:label "Indicator Removal from Tools" ;
        rdfs:subClassOf :T1027 ;
        :attack-id "T1027.005" .

    """


def _assert(actual, expected):
    if expected != actual:
        raise AssertionError(f"expected: {expected} != actual: {actual}")

def test_cases(src, g):
    """
    Test cases for updating labels and removing deprecated & revoked techniques
    Here are all the cases covered:
    -Getting all techniques & subtechniques using stix2
    -Getting all deprecated techniques & subtechniques using stix2
    -Getting all revoked techniques and subtechniques using stix2
    -Adding new techniques & subtechniques
    -Adding new deprecated technique & subtechnique
    -Adding new revoked technique & subtechnique
    -Adding correct label to technique & subtechnique that recently became deprecated
    -Modifying technique & subtechnique that recently became deprecated
    -Modifying technique & subtechnique that recently became revoked
    -Modifying technique & subtechnique that recently changed rdfs:label

    test_cases.json entries:
    1) T1020 Missing
    2) T1055.011 Missing
    3) T1053.005 Label Change
    4) T1047 Label Change
    5) T1156 Revoked by T1546.004
    6) T1175 Missing Deprecated
    7) T1026 Deprecated
    8) T1546.004 replacement for T1156
    9) T1066 Missing Revoked by T1027.005
    10) T1027.005 replacement for T1066
    11) Relationship for revoked 1
    12) Relationship for revoked 2
    13) T1174 type: course-of-action (not an attack pattern)
    14) Marking definition (not an attack-pattern)
    """

    
    # Test Case for getting techniques using stix2

    techs = get_stix_data(src, g)

    ids = ["T1020", "T1055.011", "T1053.005", "T1047", "T1156", "T1175", "T1026", "T1546.004", "T1066", "T1027.005"]
    superclasses = [["ExfiltrationTechnique"], "T1055", "T1053", ["ExecutionTechnique"], ["PersistenceTechnique"], 
                    ["LateralMovementTechnique", "ExecutionTechnique"], ["CommandAndControlTechnique"], "T1546", ["DefenseEvasionTechnique"], "T1027"]
    labels = ["Automated Exfiltration", "Extra Window Memory Injection", "Scheduled Task", "Windows Management Instrumentation", 
              "Malicious Shell Modification", "Component Object Model and Distributed COM", "Multiband Communication", 
              "Unix Shell Configuration Modification", "Indicator Removal from Tools", "Indicator Removal from Tools"]
    missing = [True, True, False, False, False, True, False, False, True, False]
    label_change = [False, False, True, True, False, False, False, True, False, False]
    deprecated = [False, False, False, False, False, True, True, False, False, False] 
    revoked = [False, False, False, False, True, False, False, False, True, False]
    revoked_by = ["", "", "", "", "T1546.004", "", "", "", "T1027.005", ""]

    for i, tech in enumerate(techs):
        _assert(tech["id"], ids[i])
        _assert(tech["superclasses"], superclasses[i])
        _assert(tech["label"], labels[i])
        _assert(tech["missing"], missing[i])
        _assert(tech["label_change"], label_change[i])
        _assert(tech["deprecated"], deprecated[i])
        _assert(tech["revoked"], revoked[i])
        _assert(tech["revoked_by"], revoked_by[i])


    # Test Case for adding new techniques 

    update_and_add(g, techs)

    # Missing 
    _assert(g.value(URIRef(_XMLNS + "T1020"), RDFS.label), Literal("Automated Exfiltration"))
    _assert(g.value(URIRef(_XMLNS + "T1020"), d3fend['attack-id']), Literal("T1020"))
    _assert(g.value(URIRef(_XMLNS + "T1020"), RDF.type), owl.Class)

    _assert(g.value(URIRef(_XMLNS + "T1055.011"), RDFS.label), Literal("Extra Window Memory Injection"))
    _assert(g.value(URIRef(_XMLNS + "T1055.011"), d3fend['attack-id']), Literal("T1055.011"))
    _assert(g.value(URIRef(_XMLNS + "T1055.011"), RDF.type), owl.Class)

    # Label Change 
    _assert(g.value(URIRef(_XMLNS + "T1047"), RDFS.label), Literal("Windows Management Instrumentation"))
    _assert(g.value(URIRef(_XMLNS + "T1047"), d3fend['attack-id']), Literal("T1047"))
    _assert(g.value(URIRef(_XMLNS + "T1047"), RDF.type), owl.Class)

    _assert(g.value(URIRef(_XMLNS + "T1053.005"), RDFS.label), Literal("Scheduled Task"))
    _assert(g.value(URIRef(_XMLNS + "T1053.005"), d3fend['attack-id']), Literal("T1053.005"))
    _assert(g.value(URIRef(_XMLNS + "T1053.005"), RDF.type), owl.Class)

    # Deprecated
    _assert(g.value(URIRef(_XMLNS + "T1026"), RDFS.label), Literal("Multiband Communication"))
    _assert(g.value(URIRef(_XMLNS + "T1026"), d3fend['attack-id']), Literal("T1026"))
    _assert(g.value(URIRef(_XMLNS + "T1026"), RDF.type), owl.Class)
    _assert(g.value(URIRef(_XMLNS + "T1026"), owl.deprecated), Literal(True))

    _assert(g.value(URIRef(_XMLNS + "T1175"), RDFS.label), Literal("Component Object Model and Distributed COM"))
    _assert(g.value(URIRef(_XMLNS + "T1175"), d3fend['attack-id']), Literal("T1175"))
    _assert(g.value(URIRef(_XMLNS + "T1175"), RDF.type), owl.Class)
    _assert(g.value(URIRef(_XMLNS + "T1175"), owl.deprecated), Literal(True))

    # Revoked 
    _assert(g.value(URIRef(_XMLNS + "T1156"), RDFS.label), Literal("Malicious Shell Modification"))
    _assert(g.value(URIRef(_XMLNS + "T1156"), d3fend['attack-id']), Literal("T1156"))
    _assert(g.value(URIRef(_XMLNS + "T1156"), RDF.type), owl.Class)
    _assert(g.value(URIRef(_XMLNS + "T1156"), owl.deprecated), Literal(True))
    _assert(g.value(URIRef(_XMLNS + "T1156"), RDFS.seeAlso), Literal("T1546.004"))
    _assert(g.value(URIRef(_XMLNS + "T1156"), RDFS.comment), Literal(f"This technique has been revoked by T1546.004"))

    _assert(g.value(URIRef(_XMLNS + "T1066"), RDFS.label), Literal("Indicator Removal from Tools"))
    _assert(g.value(URIRef(_XMLNS + "T1066"), d3fend['attack-id']), Literal("T1066"))
    _assert(g.value(URIRef(_XMLNS + "T1066"), RDF.type), owl.Class)
    _assert(g.value(URIRef(_XMLNS + "T1066"), owl.deprecated), Literal(True))
    _assert(g.value(URIRef(_XMLNS + "T1066"), RDFS.seeAlso), Literal("T1027.005"))
    _assert(g.value(URIRef(_XMLNS + "T1066"), RDFS.comment), Literal(f"This technique has been revoked by T1027.005"))

def main():
    src = MemoryStore()
    src.load_from_file("src/util/test_cases.json")
    g = Graph()
    g.parse(data=test_graph, format="turtle")
    test_cases(src, g)

if __name__ == "__main__":
    main()