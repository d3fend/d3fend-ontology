# D3FEND Ontology Conventions

1. Defensive techniques use the same IRI for a class and a named individual (OWL punning). The individual is explicitly typed as an instance of that class (for example, `:FileAnalysis a :FileAnalysis`).
1. CamelCase  [IRIs](https://en.wikipedia.org/wiki/Internationalized_Resource_Identifier), capitalize all words in the IRI fragment.
1. Labels for D3FEND defined terms must be in harmony with their IRI fragments.
    1. e.g. An IRI of `Proxy-basedWebServerAccessMediation` would have the label `Proxy-based Web Server Access Mediation`
1. Do not use bracket characters in IRIs.
1. Do not use unicode characters in IRIs.
