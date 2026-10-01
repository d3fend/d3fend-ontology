# Modular authoring prototype

Open `d3fend-protege.ttl` as the authoring entry point. It imports the modules
listed below using `catalog-v001.xml`. Imports resolve to files in this checkout;
the module IRIs do not need to be published for local development.

Every existing entity IRI is unchanged:
`http://d3fend.mitre.org/ontologies/d3fend.owl#Event`, for example, is still
`d3f:Event`. The Turtle files use `:` as an alias for that same namespace.
Each module has a distinct ontology IRI, such as
`http://d3fend.mitre.org/ontologies/modules/events`. This identifies its source
ontology without creating a new namespace for its entities.

## Source ownership

| File | Content |
|---|---|
| `modules/core.ttl` | Shared upper classes, including Event, Artifact, Technique, OffensiveTechnique, and Weakness; other shared supporting entities and axioms. |
| `modules/properties.ttl` | Object, data, and annotation property definitions. |
| `modules/artifacts.ttl` | Artifact subclasses and their named examples. |
| `modules/events.ttl` | Specialized classes below Event. |
| `modules/defensive-techniques.ttl` | Defensive techniques, tactics, and their assertions. |
| `modules/analytics.ttl` | Analytic techniques and their supporting axioms. |
| `modules/references.ttl` | Reference classes, records, and annotations about those records. |
| `external/attack.ttl` | ATT&CK classes and records, including enterprise, mobile, and ICS. |
| `external/atlas.ttl` | ATLAS classes and records. |
| `external/sparta.ttl` | SPARTA classes and records. |
| `external/cwe.ttl` | CWE classes below the shared Weakness root. |
| `external/capec.ttl` | CAPEC classes and records. |

Each named entity has one owning source file for its substantive annotations and
assertions. Keep its class and individual uses (including punning), restrictions,
and associated blank-node structures together. References to another module's
entities do not transfer ownership. OWLAPI/Protege may add bare declarations for
referenced entities when saving a module; those repeated declarations are allowed
and do not create new entities. Standalone axioms belong with the concepts they
constrain; shared upper-level axioms belong in core.

These files are authoring boundaries, and sibling modules can refer to one
another. An individual module's imports need not include every sibling's
definitions. Use the root for whole-ontology reasoning and validation. Core imports
properties; the other modules import core. The root imports all modules,
including `external/`, so the assembled ontology retains all existing content.
The prototype does not introduce a reduced core-only distribution.

The existing `mappings/`, `extensions/`, and `initiatives/` directories retain
their purposes. When adding a source module, register it in the root's imports,
the catalogs, and `ONTOLOGY_MODULES` in the repository Makefile so edits trigger
reassembly. The example initiative's catalog repeats the same mappings with
paths relative to `initiatives/`; tests check that both catalogs agree. Explicit
mappings keep the catalogs compatible with ROBOT's import resolver.

## Editing in Protege

1. Open `src/ontology/d3fend-protege.ttl` from the repository checkout.
2. Select the owning module as the active ontology before adding or editing its
   axioms. Use the root when viewing or reasoning over the complete model.
3. In new-entity preferences, choose a specified base IRI of
   `http://d3fend.mitre.org/ontologies/d3fend.owl` and the `#` separator.
   Deriving new entity IRIs from the active module would create unwanted IRIs.
4. Save changed modules and run `make format` before reviewing the diff.

Keep the committed catalog's relative paths so another checkout can resolve the
same imports. The desktop edit/save workflow still needs a manual Protege trial;
the prototype's automated checks exercise the OWLAPI through ROBOT.

## Assembly and validation

From the repository root:

```sh
make build/d3fend-asserted.ttl
make test-ontology-modules
make build/d3fend-public.ttl
```

The assembler parses each source separately, follows only explicit local catalog
mappings, removes module ontology headers and import statements, and retains the
root metadata and all entity assertions. Missing mappings or files fail the build.
It uses the existing deterministic Turtle serializer for stable output. This RDF
assembly preserves source statements before the existing ROBOT release
transforms run. The dashboard also uses this loader when reading the source root,
so its Python-only CI job can load the modules without Java.

To exercise OWLAPI import handling directly:

```sh
./bin/robot merge --catalog src/ontology/catalog-v001.xml \
  --input src/ontology/d3fend-protege.ttl \
  --output build/d3fend-import-check.ttl
```

For the initial split, the baseline was commit
`c102eefe2a158dfb73a61c6637c4df175ec8680a`. Reassembled source and baseline both
contain 40,840 asserted triples. Jena's RDF graph comparison confirmed equality
modulo blank-node identifiers. A separate comparison confirmed that ROBOT's
merged import closure equals its conversion of the original monolith.
The existing `make test` suite also passed after building the public ontology,
the control mappings, and JSON-LD output. Module tests additionally check local
import resolution, document-scoped blank nodes, ownership, and dashboard loading.

## Updating external framework content

ATT&CK, ATLAS, SPARTA, and CAPEC update commands read their owning files under
`external/` and write review candidates under `build/`. Review each candidate
against that framework's module and replace only that module when accepting the
update. The CWE extension likewise produces `build/cwe.updates.ttl`. Preserve
module ontology headers and imports. The root import file is not an update target.
