from mitreattack.stix20 import MitreAttackData
from mitreattack.stix20.custom_attack_objects import Tactic
from rdflib import XSD, Literal, Namespace, URIRef

tmfk_path = "./tmfk-stix-data/build/tmfk_attack_compatible.json"

D3FEND = Namespace("http://d3fend.mitre.org/ontologies/d3fend.owl#")
tmfk_base = "http://sec-kg.org/ontologies/tmfk"
TMFK = Namespace(tmfk_base + "#")


tmfk_data = MitreAttackData(tmfk_path)
tactics = tmfk_data.get_tactics(remove_revoked_deprecated=True)
techniques = tmfk_data.get_techniques(
    include_subtechniques=False, remove_revoked_deprecated=True
)


def D3F(iri: str) -> URIRef:
    return URIRef(D3FEND + iri)


def text(text: str, lang="en") -> str:
    return Literal(text, lang=lang)


def uri(url: str) -> str:
    return Literal(url, datatype=XSD.anyURI)


def get_id(t):
    return [
        r.external_id for r in t.external_references if r.source_name == "mitre-attack"
    ][0]


def get_ref(t):
    return [
        uri(r.url) for r in t.external_references if r.source_name == "mitre-attack"
    ][0]


def get_enabled_techs(tmfk_data: MitreAttackData, tactic: Tactic) -> list[str]:
    techniques = tmfk_data.get_techniques_by_tactic(
        tactic.get_shortname(), "enterprise-attack"
    )
    return [URIRef(TMFK + get_id(t)) for t in techniques]


def get_external_refs(tactic: Tactic) -> list[str]:
    return [
        r.url for r in tactic.external_references if r.source_name != "mitre-attack"
    ]


def get_techs_by_tactic(tactic: Tactic):
    return [
        t
        for t in tmfk_data.get_techniques_by_tactic(
            tactic_shortname=tactic.x_mitre_shortname, domain="enterprise-attack"
        )
        if t.x_mitre_is_subtechnique is False
    ]
