# D3FEND Ontology Conventions

1. Defensive Techniques are punned as instances of their parent classes.
1. CamelCase  [IRIs](https://en.wikipedia.org/wiki/Internationalized_Resource_Identifier), capitalize all words in the IRI fragment.
1. Labels for D3FEND defined terms must be in harmony with their IRI fragments.
    1. e.g. An IRI of `Proxy-basedWebServerAccessMediation` would have the label `Proxy-based Web Server Access Mediation` 
1. Do not use bracket characters in IRIs.
1. Do not use unicode characters in IRIs.

## WordNet references

Use [Open English WordNet](https://en-word.net/) for all new and updated WordNet
references, with links in the form `https://en-word.net/view/synset/{synset-id}`.
Select the exact word sense and part of speech; do not use retired Princeton
WordNet URLs. When migrating an existing reference, verify concept identity
through the Collaborative Interlingual Index (ILI), since numeric synset IDs can
differ between WordNet versions.
