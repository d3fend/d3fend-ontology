
# CWE -> D3FEND Converter

This directory holds a Makefile and documents the steps necessary to all CWE to Original add of Top-25 CWEs to d3fend-protege.ttl.  

- This only converts the Research Concepts View (aka Graph) of CWE into a D3FEND taxonomy for CWE Weaknesses.

- Future work will be required to extend this capability for ongoing CWE updates

## How to use 

To accomplish add in of CWE tree structure for the Research Concepts View (aka View 1000, Research Concepts Graph), here are the manual steps:

1. `cd extensions/cwe/`

  (i.e., go to the directory in which this README.md is located.)

2. `make install-deps` 

  This will install the # Add all CWE to Original add of Top-25 CWEs to d3fend-protege.ttl

To accomplish add in of CWE tree structure for CWE-1000 / Research
Concepts View (aka Graph), here are the manual steps.

3. `make all`

4. Review diffs to d3fend-protege.ttl manually. _Example: First time use, the Top 25 classes already present were direct subclasses of Weakness but this was no longer wanted given entire taxonomy with intermediate clases were available; statements were already there and deletions may be required_.

## Notes on RML and YARRRML technology

### RML and YARRML Introduction

RML is a declarative language for converting non-linked data formats into linked data.  RML is encoded in Turtle.  It allows extraction and tranformation steps that includes inputs from relational databases, csv, json, and xml files.  It is an extension of R2RML, which had a focus on relational data.

YARRRML is an effort to provide a more concise, and easier-to-use language for the same kinds of data transformation, where YARRRML is converted into RML and then used with RML engines.

The introduction of YARRRML as an implementation appears to be by the [RML.io](https://rml.io/) group.  The [YARRRML Parser](https://github.com/RMLio/yarrrml-parser) and [YARRRML Mapper](https://github.com/RMLio/rmlmapper-java) were developed by the group and ultimately were used for translating the CWE XML catalog file into the CWE Research Concept taxonomy of D3FEND classes representing CWE weaknesses.

### Alternative Implementations

Depending on the needs, YARRRML and RML alternatives exist.   Capabilities vary and cross-compatibility is not assured.

The Python-based [Morph KGC](https://github.com/morph-kgc/morph-kgc) (and [kglab](https://github.com/DerwenAI/kglab/), which embeds it) can use YARRRML directly to directly perform knowledge graph construction.  They also support .ttl as an output serialization format.  However, the Morph KGC team has categorized the ability to use parent references in XPath as [an enhancement rather than a bug](https://github.com/morph-kgc/morph-kgc/issues/98), which is unfortunate since RML.io's implementation and the [CARML](https://github.com/carml/carml-jar) implementation do handle parent path references in Xpath and the [RML spec](https://rml.io/specs/rml/) _[not sure what specification is considered canonical other than one on RML.io cite]_ seems to indicate this should be possible.  Intermediate RML can be generated directly in the Morph KGC with the code block:

```
rml_mapping = morph_kgc.mapping.load_yarrrml()
rml_mapping.serialize(destination="morph-kgc.rml.ttl`)
```

However, the resulting RML file did not work with other RML mapping engines.

CARML does not offer pre-built jars though appeared to be compatible with YARRRML Parser code.

Yatter did not work for RML examples tried. But minimal use, so may work out well later.

### Learning Resources 

The [RML spec](https://rml.io/specs/rml/) has many examples.

The recommendations for YARRRRML users suggested in Section 9.1 of the paper ["Path-based and triplication approaches to mapping data into RDF:
usability analysis and recommendations"](https://www.semantic-web-journal.net/system/files/swj3348.pdf) are very helpful in debugging YARRRML.

[Matey](https://rml.io/yarrrml/matey/) is live page is available for experimentning with YARRRML, but error messages are suppressed for some operations.

The many pitfalls for new users of YARRRML are noted by the ShEXML creators in their paper ["ShExML: improving the usability of heterogeneous data mapping languages for first-time users"](https://pubmed.ncbi.nlm.nih.gov/33816968/)


### Non-RML approaches

- [ShExML](https://github.com/herminiogg/ShExML)
- Python code with other RDF libraries
