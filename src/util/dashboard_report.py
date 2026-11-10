#!/usr/bin/env python3
"""Generate the static mapping dashboard report and site assets."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from defusedxml import ElementTree as ET
from rdflib import Graph, URIRef
from rdflib.namespace import RDFS
from rdflib.util import guess_format


D3F_PREFIX = "http://d3fend.mitre.org/ontologies/d3fend.owl#"

DEFAULT_SOURCE_PATHS = (
    "build/d3fend-public-with-controls.ttl",
    "build/d3fend-public.ttl",
    "src/ontology/d3fend-protege.ttl",
)

ONTOLOGY_RELATION_QUERIES = (
    "semantic-relation-property-assertions.rq",
    "semantic-relation-class-restrictions.rq",
)

ONTOLOGY_METADATA_QUERY = "ontology-release-metadata.rq"

D3FEND_COMPACT_IRI_PATTERN = re.compile(r"\bd3f:([A-Za-z][A-Za-z0-9_-]*)\b")


@dataclass(frozen=True)
class Framework:
    id: str
    label: str
    sort_order: int
    kind: str
    item_queries: tuple[str, ...] = ()
    link_queries: tuple[str, ...] = ()


@dataclass(frozen=True)
class DashboardItem:
    iri: str
    compact_iri: str
    external_id: str | None
    label: str
    source_version: str | None
    url: str | None = None


@dataclass(frozen=True)
class Relation:
    framework_id: str
    item: str
    predicate: str
    predicate_label: str
    target: str
    target_label: str


@dataclass(frozen=True)
class DashboardConfig:
    source_versions: dict[str, str]
    attack_item_url_prefix: str
    atlas_item_url_prefix: str
    sparta_item_url_prefix: str
    capec_item_url_prefix: str
    cwe_item_url_prefix: str
    ocsf_schema_prefix: str
    ocsf_source_version: str
    nist_source_version: str
    nist_iri_version: str
    nist_item_url_prefix: str
    cci_source_version: str
    cci_mapping_version: str
    cci_item_url: str


def compact_uri(value):
    text = str(value)
    if text.startswith(D3F_PREFIX):
        return "d3f:" + text.removeprefix(D3F_PREFIX)
    hash_index = text.rfind("#")
    slash_index = text.rstrip("/").rfind("/")
    split_index = max(hash_index, slash_index)
    if split_index > -1:
        return text.rsplit(text[split_index], 1)[-1]
    return text


def text_value(value):
    if value is None:
        return None
    text = str(value)
    return text if text else None


def parse_graph(source_path):
    graph = Graph()
    graph.parse(source_path, format=guess_format(str(source_path)))
    return graph


def select_source(cli_source):
    if cli_source:
        source = Path(cli_source)
        if not source.exists():
            raise FileNotFoundError(source)
        return source

    for source in DEFAULT_SOURCE_PATHS:
        path = Path(source)
        if path.exists():
            return path

    raise FileNotFoundError("No dashboard source ontology found")


FRAMEWORKS = (
    Framework(
        id="attack-enterprise",
        label="ATT&CK Enterprise",
        sort_order=10,
        kind="ontology",
        item_queries=("attack-enterprise-technique-members.rq",),
    ),
    Framework(
        id="attack-ics",
        label="ATT&CK ICS",
        sort_order=20,
        kind="ontology",
        item_queries=("attack-ics-technique-members.rq",),
    ),
    Framework(
        id="attack-mobile",
        label="ATT&CK Mobile",
        sort_order=30,
        kind="ontology",
        item_queries=("attack-mobile-technique-members.rq",),
    ),
    Framework(
        id="atlas",
        label="ATLAS",
        sort_order=40,
        kind="ontology",
        item_queries=("atlas-technique-members.rq",),
    ),
    Framework(
        id="sparta",
        label="SPARTA",
        sort_order=50,
        kind="ontology",
        item_queries=("sparta-technique-members.rq",),
    ),
    Framework(
        id="capec",
        label="CAPEC",
        sort_order=60,
        kind="ontology",
        item_queries=("capec-attack-pattern-members.rq",),
    ),
    Framework(
        id="cwe",
        label="CWE",
        sort_order=70,
        kind="ontology",
        item_queries=("cwe-weakness-members.rq",),
    ),
    Framework(
        id="nist-800-53",
        label="NIST SP 800-53",
        sort_order=80,
        kind="source-table",
    ),
    Framework(
        id="cci",
        label="CCI",
        sort_order=90,
        kind="source-table",
    ),
    Framework(
        id="ocsf",
        label="OCSF",
        sort_order=100,
        kind="ocsf-schema",
        link_queries=("ocsf-schema-reference-links.rq",),
    ),
)


def read_query(query_dir, query_file):
    query_path = query_dir / query_file
    if not query_path.exists():
        raise FileNotFoundError(query_path)
    return query_path.read_text()


def query_dicts(graph, query_dir, query_file):
    result = graph.query(read_query(query_dir, query_file))
    variable_names = [str(variable) for variable in result.vars]
    return [dict(zip(variable_names, row)) for row in result]


def slash_url(prefix, *parts, trailing_slash=True):
    path = "/".join(quote(str(part), safe="") for part in parts if str(part))
    suffix = "/" if trailing_slash else ""
    return f"{prefix.rstrip('/')}/{path}{suffix}"


def attack_url(external_id, config):
    parts = str(external_id).split(".", 1)
    if len(parts) == 2:
        return slash_url(config.attack_item_url_prefix, parts[0], parts[1])
    return slash_url(config.attack_item_url_prefix, external_id)


def atlas_url(external_id, config):
    return slash_url(
        config.atlas_item_url_prefix,
        external_id,
        trailing_slash=False,
    )


def sparta_url(external_id, config):
    parts = str(external_id).split(".")
    return slash_url(config.sparta_item_url_prefix, *parts)


def capec_url(external_id, config):
    capec_id = str(external_id).removeprefix("CAPEC-")
    return f"{config.capec_item_url_prefix.rstrip('/')}/{quote(capec_id, safe='')}.html"


def cwe_url(external_id, config):
    cwe_id = str(external_id).removeprefix("CWE-")
    return f"{config.cwe_item_url_prefix.rstrip('/')}/{quote(cwe_id, safe='')}.html"


def nist_control_url(control_id, config):
    normalized = str(control_id).strip().lower().replace(" ", "")
    family, _, _ = normalized.partition("-")
    base_control = normalized.split("(", 1)[0]
    family_path = quote(family, safe="")
    base_path = quote(base_control, safe="")
    url = slash_url(config.nist_item_url_prefix, family_path, base_path)
    enhancement = re.search(r"\(([^)]+)\)", normalized)
    if enhancement:
        enhancement_path = quote(enhancement.group(1), safe="")
        url = f"{url}{base_path}-{enhancement_path}/"
    return url


def cci_url(_external_id, config):
    return config.cci_item_url


def framework_item_url(framework_id, external_id, config):
    if not external_id:
        return None
    builders = {
        "attack-enterprise": attack_url,
        "attack-ics": attack_url,
        "attack-mobile": attack_url,
        "atlas": atlas_url,
        "sparta": sparta_url,
        "capec": capec_url,
        "cwe": cwe_url,
        "nist-800-53": nist_control_url,
        "cci": cci_url,
    }
    builder = builders.get(framework_id)
    return builder(external_id, config) if builder else None


def load_frameworks():
    return sorted(FRAMEWORKS, key=lambda framework: framework.sort_order)


def load_items(graph, query_dir, frameworks, config):
    items_by_framework = defaultdict(dict)
    for framework in frameworks:
        if framework.kind != "ontology":
            continue
        for query_file in framework.item_queries:
            for row in query_dicts(graph, query_dir, query_file):
                iri = str(row["item"])
                label = text_value(row.get("label")) or compact_uri(iri)
                external_id = text_value(row.get("external_id"))
                source_version = config.source_versions.get(framework.id)
                items_by_framework[framework.id][iri] = DashboardItem(
                    iri=iri,
                    compact_iri=compact_uri(iri),
                    external_id=external_id,
                    label=label,
                    source_version=source_version,
                    url=framework_item_url(framework.id, external_id, config),
                )
    return items_by_framework


def cell_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def nist_display_id(control_id):
    text = str(control_id).strip().upper()
    if "." not in text:
        return text
    base, enhancement = text.split(".", 1)
    return f"{base}({enhancement})"


def nist_control_iri(control_id, iri_version):
    control_iri_name = control_id.replace(" ", "")
    control_iri_name = control_iri_name.replace(")", "")
    control_iri_name = control_iri_name.replace("(", "_")
    return D3F_PREFIX + f"NIST_SP_800-53_R{iri_version}_{control_iri_name}"


def iter_nist_controls(control):
    yield control
    for child in control.get("controls", ()) or ():
        yield from iter_nist_controls(child)


def load_nist_control_items(source_path, config):
    catalog = read_json(source_path)["catalog"]
    items = {}
    for group in catalog.get("groups", ()) or ():
        for root_control in group.get("controls", ()) or ():
            for control in iter_nist_controls(root_control):
                control_id = nist_display_id(control["id"])
                control_name = text_value(control.get("title"))
                iri = nist_control_iri(control_id, config.nist_iri_version)
                items[iri] = DashboardItem(
                    iri=iri,
                    compact_iri=compact_uri(iri),
                    external_id=control_id,
                    label=f"{control_id} {control_name}"
                    if control_name
                    else control_id,
                    source_version=config.nist_source_version,
                    url=framework_item_url("nist-800-53", control_id, config),
                )
    return items


def cci_control_iri(cci_id, mapping_version):
    return D3F_PREFIX + f"{cci_id}_v{mapping_version}"


def namespaced(root, name):
    if not root.tag.startswith("{"):
        return name
    namespace = root.tag[1:].split("}", 1)[0]
    return f"{{{namespace}}}{name}"


def xml_child_text(root, item, name):
    child = item.find(namespaced(root, name))
    if child is None:
        return None
    return cell_text(child.text)


def load_cci_control_items(source_path, config):
    root = ET.parse(source_path).getroot()
    items = {}
    for item in root.findall(f".//{namespaced(root, 'cci_item')}"):
        cci_id = cell_text(item.get("id"))
        status = xml_child_text(root, item, "status")
        if not cci_id or status == "deprecated":
            continue
        iri = cci_control_iri(cci_id, config.cci_mapping_version)
        items[iri] = DashboardItem(
            iri=iri,
            compact_iri=compact_uri(iri),
            external_id=cci_id,
            label=cci_id,
            source_version=config.cci_source_version,
            url=framework_item_url("cci", cci_id, config),
        )
    return items


def ocsf_url(path, config):
    return config.ocsf_schema_prefix.rstrip("/") + "/" + path.strip("/")


def ocsf_path(url, config):
    text = str(url).rstrip("/")
    prefix = config.ocsf_schema_prefix.rstrip("/") + "/"
    if text.startswith(prefix):
        return text.removeprefix(prefix)
    return text


def ocsf_label(name, data):
    caption = text_value(data.get("caption"))
    if caption:
        return caption
    return name.replace("_", " ").title()


def read_json(path):
    return json.loads(path.read_text())


def require_ocsf_schema(schema_dir):
    version_path = schema_dir / "version.json"
    if not version_path.exists():
        raise FileNotFoundError(
            f"{version_path} not found. Run `make download-ocsf` first."
        )


def add_ocsf_item(items, iri, label, version, config):
    iri = iri.rstrip("/")
    items.setdefault(
        iri,
        DashboardItem(
            iri=iri,
            compact_iri=ocsf_path(iri, config),
            external_id=ocsf_path(iri, config),
            label=label,
            source_version=version,
            url=iri,
        ),
    )


def load_ocsf_categories(schema_dir, version, items, config):
    categories_path = schema_dir / "categories.json"
    categories = read_json(categories_path).get("attributes", {})
    for name, data in categories.items():
        add_ocsf_item(
            items,
            ocsf_url(f"categories/{name}", config),
            ocsf_label(name, data),
            version,
            config,
        )


def load_ocsf_schema_files(root, url_prefix, version, items, config):
    if not root.exists():
        return
    for path in sorted(root.rglob("*.json")):
        data = read_json(path)
        name = path.stem
        if name.startswith("_"):
            continue
        add_ocsf_item(
            items,
            ocsf_url(f"{url_prefix}/{name}", config),
            ocsf_label(name, data),
            version,
            config,
        )


def extension_name(extension_dir):
    extension_path = extension_dir / "extension.json"
    if not extension_path.exists():
        return extension_dir.name
    return text_value(read_json(extension_path).get("name")) or extension_dir.name


def load_ocsf_extension_files(schema_dir, version, items, config):
    extensions_dir = schema_dir / "extensions"
    if not extensions_dir.exists():
        return
    for extension_dir in sorted(
        path for path in extensions_dir.iterdir() if path.is_dir()
    ):
        extension = extension_name(extension_dir)
        load_ocsf_schema_files(
            extension_dir / "events",
            f"classes/{extension}",
            version,
            items,
            config,
        )
        load_ocsf_schema_files(
            extension_dir / "objects",
            "objects",
            version,
            items,
            config,
        )


def load_ocsf_schema_items(schema_dir, config):
    require_ocsf_schema(schema_dir)
    version = config.ocsf_source_version
    items = {}
    load_ocsf_categories(schema_dir, version, items, config)
    load_ocsf_schema_files(schema_dir / "events", "classes", version, items, config)
    load_ocsf_schema_files(schema_dir / "objects", "objects", version, items, config)
    load_ocsf_extension_files(schema_dir, version, items, config)
    return items


def iter_ocsf_schema_documents(schema_dir, config):
    document_specs = [
        (schema_dir / "events", "classes"),
        (schema_dir / "objects", "objects"),
    ]
    extensions_dir = schema_dir / "extensions"
    if extensions_dir.exists():
        for extension_dir in sorted(
            path for path in extensions_dir.iterdir() if path.is_dir()
        ):
            extension = extension_name(extension_dir)
            document_specs.extend(
                [
                    (extension_dir / "events", f"classes/{extension}"),
                    (extension_dir / "objects", "objects"),
                ]
            )

    for root, url_prefix in document_specs:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.json")):
            if path.stem.startswith("_"):
                continue
            yield ocsf_url(f"{url_prefix}/{path.stem}", config), read_json(path)


def iter_ocsf_references(value):
    if isinstance(value, dict):
        references = value.get("references")
        if isinstance(references, list):
            for reference in references:
                if isinstance(reference, dict):
                    yield reference
        elif isinstance(references, dict):
            yield references

        for child_key, child_value in value.items():
            if child_key == "references":
                continue
            yield from iter_ocsf_references(child_value)
    elif isinstance(value, list):
        for child_value in value:
            yield from iter_ocsf_references(child_value)


def d3f_iri_from_ocsf_reference(reference):
    text = " ".join(str(reference.get(field, "")) for field in ("url", "description"))
    match = D3FEND_COMPACT_IRI_PATTERN.search(text)
    if not match:
        return None
    return D3F_PREFIX + match.group(1)


def ontology_label(graph, iri):
    label = graph.value(URIRef(iri), RDFS.label)
    return text_value(label) or compact_uri(iri)


def load_ocsf_schema_reference_relations(schema_dir, graph, config):
    relations = []
    seen = set()
    for schema_url, data in iter_ocsf_schema_documents(schema_dir, config):
        target = schema_url.rstrip("/")
        target_label = ocsf_path(target, config).replace("/", ": ")
        for reference in iter_ocsf_references(data):
            subject = d3f_iri_from_ocsf_reference(reference)
            if not subject:
                continue
            key = (subject, target)
            if key in seen:
                continue
            seen.add(key)
            relations.append(
                {
                    "subject": subject,
                    "subject_label": ontology_label(graph, subject),
                    "predicate": "https://schema.ocsf.io/references",
                    "predicate_label": "schema reference",
                    "target": target,
                    "target_label": target_label,
                    "source_version": config.ocsf_source_version,
                }
            )
    return relations


def framework_ids_by_item(items_by_framework):
    item_frameworks = defaultdict(set)
    for framework_id, framework_items in items_by_framework.items():
        for item_iri in framework_items:
            item_frameworks[item_iri].add(framework_id)
    return item_frameworks


def load_relations(graph, query_dir, items_by_framework):
    item_frameworks = framework_ids_by_item(items_by_framework)
    relation_keys = set()
    relations = []

    for query_file in ONTOLOGY_RELATION_QUERIES:
        for row in query_dicts(graph, query_dir, query_file):
            item = str(row["item"])
            predicate = str(row["predicate"])
            predicate_label = text_value(row.get("predicate_label")) or compact_uri(
                predicate
            )
            target = str(row["target"])
            target_label = text_value(row.get("target_label")) or compact_uri(target)
            for framework_id in item_frameworks.get(item, ()):
                key = (framework_id, item, predicate, target)
                if key in relation_keys:
                    continue
                relation_keys.add(key)
                relations.append(
                    Relation(
                        framework_id=framework_id,
                        item=item,
                        predicate=predicate,
                        predicate_label=predicate_label,
                        target=target,
                        target_label=target_label,
                    )
                )
    return relations


def relations_by_framework(relations):
    grouped = defaultdict(list)
    for relation in relations:
        grouped[relation.framework_id].append(relation)
    return grouped


def is_integrating_relation(relation, current_items, all_items):
    if relation.target == relation.item:
        return False
    if relation.target in current_items:
        return False
    if relation.target.startswith(D3F_PREFIX):
        return True
    return relation.target in all_items


def predicate_summary(predicate_counts):
    return [
        {"label": predicate, "count": count}
        for predicate, count in predicate_counts.most_common()
    ]


def source_version(values):
    versions = sorted({value for value in values if value})
    if not versions:
        return "unknown"
    return ", ".join(versions)


def relation_payload(relation):
    return {
        "predicate": relation.predicate,
        "predicate_label": relation.predicate_label,
        "target": relation.target,
        "target_compact_iri": compact_uri(relation.target),
        "target_label": relation.target_label,
    }


def ontology_item_payload(item, item_relations):
    return {
        "iri": item.iri,
        "compact_iri": item.compact_iri,
        "external_id": item.external_id,
        "label": item.label,
        "source_version": item.source_version,
        "url": item.url,
        "mapped": bool(item_relations),
        "relationship_count": len(item_relations),
        "relations": [relation_payload(relation) for relation in item_relations],
    }


def summarize_ontology_framework(framework, items, relations, all_items):
    item_iris = set(items)
    integrated = set()
    predicate_counts = Counter()
    relationship_count = 0
    integrating_relations = defaultdict(list)

    for relation in relations:
        if relation.item not in item_iris:
            continue
        if not is_integrating_relation(relation, item_iris, all_items):
            continue
        integrated.add(relation.item)
        integrating_relations[relation.item].append(relation)
        predicate_counts[relation.predicate_label] += 1
        relationship_count += 1

    included_count = len(items)
    integrated_count = len(integrated)
    coverage = (
        round((integrated_count / included_count) * 100, 1) if included_count else None
    )
    item_details = sorted(
        (
            ontology_item_payload(item, integrating_relations[iri])
            for iri, item in items.items()
        ),
        key=lambda item: item["label"],
    )

    return {
        "id": framework.id,
        "label": framework.label,
        "source_version": source_version(
            item.source_version for item in items.values()
        ),
        "included_count": included_count,
        "integrated_count": integrated_count,
        "unmapped_count": included_count - integrated_count,
        "coverage_percent": coverage,
        "relationship_count": relationship_count,
        "relations_by_predicate": predicate_summary(predicate_counts),
        "items": item_details,
    }


def link_relation_values(framework, row, config):
    target = str(row["target"])
    if framework.id == "ocsf":
        schema_prefix = config.ocsf_schema_prefix.rstrip("/") + "/"
        if not target.startswith(schema_prefix):
            return None
        target_label = ocsf_path(target, config).replace("/", ": ")
        source_version = config.ocsf_source_version
    else:
        target_label = text_value(row.get("target_label")) or compact_uri(row["target"])
        source_version = text_value(row.get("source_version"))

    return {
        "subject": str(row["subject"]),
        "subject_label": text_value(row.get("subject_label"))
        or compact_uri(row["subject"]),
        "predicate": str(row["predicate"]),
        "predicate_label": text_value(row.get("predicate_label"))
        or compact_uri(row["predicate"]),
        "target": target,
        "target_label": target_label,
        "source_version": source_version,
    }


def load_link_relations(graph, query_dir, frameworks, config):
    grouped = defaultdict(list)
    for framework in frameworks:
        for query_file in framework.link_queries:
            for row in query_dicts(graph, query_dir, query_file):
                relation = link_relation_values(framework, row, config)
                if relation:
                    grouped[framework.id].append(relation)
    return grouped


def link_relation_payload(relation):
    return {
        "predicate": relation["predicate"],
        "predicate_label": relation["predicate_label"],
        "target": relation["target"],
        "target_compact_iri": relation["target_label"],
        "target_label": relation["target_label"],
    }


def ocsf_relation_payload(relation):
    return {
        "predicate": relation["predicate"],
        "predicate_label": relation["predicate_label"],
        "target": relation["subject"],
        "target_compact_iri": compact_uri(relation["subject"]),
        "target_label": relation["subject_label"],
    }


def ocsf_item_payload(item, item_relations):
    return {
        "iri": item.iri,
        "compact_iri": item.compact_iri,
        "external_id": item.external_id,
        "label": item.label,
        "source_version": item.source_version,
        "url": item.url,
        "mapped": bool(item_relations),
        "relationship_count": len(item_relations),
        "relations": [ocsf_relation_payload(relation) for relation in item_relations],
    }


def link_item_payload(subject, relations):
    first_relation = relations[0]
    return {
        "iri": subject,
        "compact_iri": compact_uri(subject),
        "external_id": None,
        "label": first_relation["subject_label"],
        "source_version": first_relation["source_version"],
        "url": None,
        "mapped": True,
        "relationship_count": len(relations),
        "relations": [link_relation_payload(relation) for relation in relations],
    }


def summarize_ocsf_framework(framework, items, link_relations):
    relations_by_schema_target = defaultdict(list)
    out_of_schema_links = []
    for relation in link_relations:
        target = str(relation["target"]).rstrip("/")
        if target in items:
            relations_by_schema_target[target].append(relation)
        else:
            out_of_schema_links.append(relation)

    predicate_counts = Counter(
        relation["predicate_label"]
        for relations in relations_by_schema_target.values()
        for relation in relations
    )
    item_details = sorted(
        (
            ocsf_item_payload(item, relations_by_schema_target.get(iri, ()))
            for iri, item in items.items()
        ),
        key=lambda item: item["label"],
    )
    included_count = len(items)
    integrated_count = len(relations_by_schema_target)
    coverage = (
        round((integrated_count / included_count) * 100, 1) if included_count else None
    )

    return {
        "id": framework.id,
        "label": framework.label,
        "source_version": source_version(
            item.source_version for item in items.values()
        ),
        "included_count": included_count,
        "integrated_count": integrated_count,
        "unmapped_count": included_count - integrated_count,
        "coverage_percent": coverage,
        "relationship_count": sum(
            len(relations) for relations in relations_by_schema_target.values()
        ),
        "out_of_schema_relationship_count": len(out_of_schema_links),
        "relations_by_predicate": predicate_summary(predicate_counts),
        "items": item_details,
    }


def summarize_link_framework(framework, link_relations):
    relations_by_subject = defaultdict(list)
    for relation in link_relations:
        relations_by_subject[relation["subject"]].append(relation)

    targets = {relation["target"] for relation in link_relations}
    predicate_counts = Counter(
        relation["predicate_label"] for relation in link_relations
    )
    item_details = sorted(
        (
            link_item_payload(subject, relations)
            for subject, relations in relations_by_subject.items()
        ),
        key=lambda item: item["label"],
    )

    return {
        "id": framework.id,
        "label": framework.label,
        "source_version": source_version(
            relation["source_version"] for relation in link_relations
        ),
        "included_count": len(item_details),
        "integrated_count": len(item_details),
        "unmapped_count": 0,
        "coverage_percent": 100 if item_details else None,
        "relationship_count": len(link_relations),
        "target_count": len(targets),
        "relations_by_predicate": predicate_summary(predicate_counts),
        "items": item_details,
    }


def ontology_metadata(graph, query_dir):
    rows = query_dicts(graph, query_dir, ONTOLOGY_METADATA_QUERY)
    row = rows[0] if rows else {}
    return {
        "version": text_value(row.get("version")),
        "release_date": text_value(row.get("release_date")),
        "triple_count": int(row.get("triple_count") or 0),
    }


def build_report(
    source_path,
    query_dir,
    ocsf_schema_dir,
    nist_source_path,
    cci_source_path,
    config,
):
    graph = parse_graph(source_path)
    frameworks = load_frameworks()
    items_by_framework = load_items(graph, query_dir, frameworks, config)
    items_by_framework["nist-800-53"] = load_nist_control_items(
        nist_source_path,
        config,
    )
    items_by_framework["cci"] = load_cci_control_items(cci_source_path, config)
    items_by_framework["ocsf"] = load_ocsf_schema_items(ocsf_schema_dir, config)
    relation_groups = relations_by_framework(
        load_relations(graph, query_dir, items_by_framework)
    )
    link_groups = load_link_relations(graph, query_dir, frameworks, config)
    link_groups["ocsf"].extend(
        load_ocsf_schema_reference_relations(ocsf_schema_dir, graph, config)
    )
    all_item_iris = {
        item_iri
        for framework_items in items_by_framework.values()
        for item_iri in framework_items
    }

    framework_reports = []
    for framework in frameworks:
        if framework.kind == "ocsf-schema":
            framework_reports.append(
                summarize_ocsf_framework(
                    framework,
                    items_by_framework[framework.id],
                    link_groups[framework.id],
                )
            )
            continue
        if framework.kind == "link":
            framework_reports.append(
                summarize_link_framework(framework, link_groups[framework.id])
            )
            continue
        framework_reports.append(
            summarize_ontology_framework(
                framework,
                items_by_framework[framework.id],
                relation_groups[framework.id],
                all_item_iris,
            )
        )

    totals = {
        "included_count": sum(item["included_count"] for item in framework_reports),
        "integrated_count": sum(item["integrated_count"] for item in framework_reports),
        "relationship_count": sum(
            item["relationship_count"] for item in framework_reports
        ),
    }

    return {
        "schema_version": 3,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_path": str(source_path),
        "ontology": ontology_metadata(graph, query_dir),
        "totals": totals,
        "frameworks": framework_reports,
    }


def write_report(report, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def write_site(report_path, template_path, site_dir):
    site_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, site_dir / "index.html")
    shutil.copyfile(report_path, site_dir / "dashboard-report.json")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Ontology file to analyze")
    parser.add_argument(
        "--query-dir",
        default="src/queries",
        help="Directory containing SPARQL report queries",
    )
    parser.add_argument(
        "--ocsf-schema-dir",
        required=True,
        help="Downloaded OCSF schema directory",
    )
    parser.add_argument("--ocsf-schema-prefix", required=True)
    parser.add_argument("--ocsf-source-version", required=True)
    parser.add_argument(
        "--nist-source",
        required=True,
        help="Downloaded NIST SP 800-53 catalog JSON used for the dashboard denominator",
    )
    parser.add_argument("--nist-source-version", required=True)
    parser.add_argument("--nist-iri-version", required=True)
    parser.add_argument("--nist-item-url-prefix", required=True)
    parser.add_argument(
        "--cci-source",
        required=True,
        help="Downloaded CCI XML catalog used for the dashboard denominator",
    )
    parser.add_argument("--cci-source-version", required=True)
    parser.add_argument("--cci-mapping-version", required=True)
    parser.add_argument("--cci-item-url", required=True)
    parser.add_argument("--attack-version", required=True)
    parser.add_argument("--attack-item-url-prefix", required=True)
    parser.add_argument("--atlas-version", required=True)
    parser.add_argument("--atlas-item-url-prefix", required=True)
    parser.add_argument("--sparta-version", required=True)
    parser.add_argument("--sparta-item-url-prefix", required=True)
    parser.add_argument("--capec-version", required=True)
    parser.add_argument("--capec-item-url-prefix", required=True)
    parser.add_argument("--cwe-version", required=True)
    parser.add_argument("--cwe-item-url-prefix", required=True)
    parser.add_argument(
        "--report",
        default="reports/dashboard-report.json",
        help="Report JSON output path",
    )
    parser.add_argument(
        "--site-dir",
        default="dist/dashboard",
        help="Static dashboard output directory",
    )
    parser.add_argument(
        "--template",
        default="src/dashboard/index.html",
        help="Dashboard HTML template path",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write only the structured JSON report",
    )
    return parser.parse_args()


def build_config(args):
    return DashboardConfig(
        source_versions={
            "attack-enterprise": args.attack_version,
            "attack-ics": args.attack_version,
            "attack-mobile": args.attack_version,
            "atlas": args.atlas_version,
            "sparta": args.sparta_version,
            "capec": args.capec_version,
            "cwe": args.cwe_version,
        },
        attack_item_url_prefix=args.attack_item_url_prefix,
        atlas_item_url_prefix=args.atlas_item_url_prefix,
        sparta_item_url_prefix=args.sparta_item_url_prefix,
        capec_item_url_prefix=args.capec_item_url_prefix,
        cwe_item_url_prefix=args.cwe_item_url_prefix,
        ocsf_schema_prefix=args.ocsf_schema_prefix,
        ocsf_source_version=args.ocsf_source_version,
        nist_source_version=args.nist_source_version,
        nist_iri_version=args.nist_iri_version,
        nist_item_url_prefix=args.nist_item_url_prefix,
        cci_source_version=args.cci_source_version,
        cci_mapping_version=args.cci_mapping_version,
        cci_item_url=args.cci_item_url,
    )


def main():
    args = parse_args()
    source_path = select_source(args.source)
    report_path = Path(args.report)
    config = build_config(args)
    report = build_report(
        source_path,
        Path(args.query_dir),
        Path(args.ocsf_schema_dir),
        Path(args.nist_source),
        Path(args.cci_source),
        config,
    )
    write_report(report, report_path)
    if not args.report_only:
        write_site(report_path, Path(args.template), Path(args.site_dir))
    print(f"Wrote {report_path}")
    if not args.report_only:
        print(f"Wrote {Path(args.site_dir) / 'index.html'}")


if __name__ == "__main__":
    main()
