# D3FEND Ontology Change Log

## Version - 1.2.0 - 2025-08-01

 - Add inbound internet web and encrypted traffic artifacts. (#442)
 - Introduce initial network node relationships and refactor server and service interactions. (#437)
 - Remove assertions of owl:topObjectProperty and owl:topDataProperty. (#432)
 - Rename d3f:CollectorAgent to d3f:NetworkAgent. (#433)
 - Enhance event taxonomy relationships and add application event associations. (#416)
 - Add configuration modification events and relate them to application updates. (#419)
 - Add physical link event definitions. (#420)
 - Add rdfs:label annotations for signs and signed-by properties. (#418)
 - Add definitions to terms and apply editorial fixes. (#409)
 - Update CWE version to 4.17 and add definitions and synonyms for each weakness. (#411)
 - Update definition for continuous mediation at the top-level class. (#399)
 - Add 'identity' to D3-AM definition and update access modeling relationships. (#400)
 - Fix techniques display on the matrix. (#408)
 - Update OT command and event taxonomy with definition and synonym fixes. (#402)
 - Add missing d3f:definition to d3f:erases. (#404)
 - Fix report summary target in Makefile. (#396)
 - Add d3f:PackageURL to identify software packages. (#401)

## Version - 1.1.0 - 2025-04-21

 - Added initial precedence relationships between digital events. (#380)
 - Added initial set of OT commands, events, and countermeasures. (#386)
 - Added Bus Network concepts. (#392)
 - Added missing tactic to CSV cleaning script. (#382)
 - README.md now states that POSIX is required to build a distribution. (#349)
 - Updated definitions to distinguish D3-LFAM and D3-LFP. (#367)
 - Updated CI pipeline because of github changes.
 - Updated D3-FE, extended and revised references. (#366)
 - Added NIST identifier to title of new references.
 - Extended and revised KB article for D3-FE.
 - Resolved malformed URL for has-link assertion. (#347)
 - Fix IRI formatting to be proper style. (#294)
 - Corrected assertion: A d3f:TertiaryStorage device is a d3f:MemoryBlock. (#346)
 - Defined inverse relationship: d3f:recorded-in. (#343)
 - Added Content Disarm and Reconstruct techniques. (#381)
 - Added taxonomy for data and data-hardening techniques. (#259)
 - Added risk properties: risk-impact and risk-likelihood. (#369)
 - Added definitions for offensive tactics. (#352)

## Version - 1.0.0 - 2024-12-20

 - Define D3FEND Digital Event ontology with deeper OCSF integration. (#326)
 - ATT&CK Data Sources integration and related digital artifacts. (#317)
 - Add Access Mediation techniques with zero-trust alignment. (#336)
 - Refine auth events to align with Access Mediation techniques. (#328)
 - Add Source Code Hardening techniques to ontology. (#325)
 - Add Credential Scrubbing as Source Code Hardening technique. (#333)
 - Introduce an upper model for D3FEND OT artifacts. (#329)
 - Add Cloud Service Provider. (#319)
 - Application-based Process Isolation. (#320)
 - First D3FEND-CCO mappings. (#296)
 - Carve out D3FEND catalog classes and properties into separate file. (#338)
 - Update to ATT&CK Enterprise v16.0. (#315)
 - Add Python scripts to automate the import of CAPEC into D3FEND. (#258)
 - Add missing rdfs:labels. (#332)
 - Align T1087 subtechniques with correct parent. (#295)

## Version - 0.17.0 - 2024-10-11

 - Promote Link to core and initial major refactor to D3FEND Core. (#248)
 - Cleanup anonymous individuals and fix network model. (#305)
 - Update make all order and upgrade CCO with working link.
 - New Evict and Restore techniques. (#240)
 - Major clean up on Network Node taxonomy, rename Platform to Computer Platform. (#301)
 - Add Condition to core. (#298)
 - Align definition of d3f:T1205 with ATT&CK. (#291)
 - Add optional custom pki trust config to Dockerfile. (#286)
 - Add new property, fix missing label, and new system calls. (#244)
 - Make d3f:Restore a named individual. (#278)
 - Update dependencies and CI to new github docker setup. (#280)
 - Fix typo in definition of OSAPISystemFunction. (#235)
 - Get Running Processes enumerates Process. (#231)
 - Add "unloads" property. (#230)


## Version - 0.16.0 - 2024-07-10

 - Replace rdfs:seeAlso and rdfs:isDefinedBy anyURIs with standard IRIs. (#263)
 - Removed hidden Reverse Resolution Domain Denylisting class. (#252)
 - Direct Physical Link Mapping Technique added, deleted hidden Passive Physical Link Mapping class. (#251)
 - Complete Certificate-based Authentication technique. (#250)
 - Update to ATT&CK 15. (#239)
 - Fix typo in definition of OSAPISystemFunction. (#235)
 - GetRunningProcesses enumerates Process. (#231)
 - Add "unloads" property. (#230)

## Version - 0.15.0 - 2024-04-26

 - Fix d3fend-id on Reissue Credential. (#234)
 - Create initial abstraction for additional threat models in addition to ATT&CK. (#233)
 - Add system call GetRunningProcesses. (#231)
 - Additional artifacts for more detailed modeling of process injection. (#228) (#217)
 - Replace some Unicode UTF-8 characters with ASCII look-alikes. (#223)
 - Add Adding NtOpenThread artifact. (#220)
 - Added System Shutdown/Reboot Technique. (#202)
 - Create initial abstraction of new D3FEND Core model. (#212)
 - Fix typo in URL. (#201)
 - Improve update_attack to handle definitions. (#209)
 - Update artifact for Organization Mapping. (#103)
 - Fixed URIs ending with hash signs cause Protege problems. (#221)
 - Add CWE taxonomy from children of pillars down to support D3FEND / CWE mapping queries. (#184)


## Version - 0.14.0 - 2024-01-26

 - New Container Image Analysis technique. (#37)
 - Updates refereces to Certificate Pinning and addtional minor bugfixes. (#207)
 - Added digital artifact for T1542. (#211)


## Version - 0.13.0-BETA-1 - 2023-10-30

- New "Restore" tactic and taxonomy of restore techniques. (#173)
- New Analytic Technique Taxonomy and Analytic Characterization Framework.
- Integrate full CWE taxonomy. (#189)
- Added Digital Artifacts for MSHTA Execution.
- Inferred D3FEND countermeasures for CWEs now visualized and with API. (#184)
- Link D3FEND classes to OCSF objects. (#178)
- Refactor csv build and fix double definitions. (#180)
- New defensive technique: Email Filtering. (#172)
- Major refactor of ATT&CK updater script. (#188)


## Version - 0.12.0-BETA-2 - 2023-03-21

- Add missing identifier for D3-IAA

## Version - 0.12.0-BETA-1 - 2023-01-31

- Updated ATT&CK mappings.
- Added PythonScript subClassOf ExecutableScript. (#101)
- Added defensive techniques: FileEviction techniques (#92, #93), Identifier Activity Analysis (#95), Data and Data Hardening Techniques. (#75)
- Added digital artifacts: URL Reputation Analsyis (#71), Network Traffic Analysis software (#79) Network Traffic Analysis Software. (#80)
- Added top #25 Weaknesses from CWE and relationships to digital artifacts, including new subroutine taxonomy. (#66)
- Fixed errata on version data property (#89) Physical Object subclassing. (#88)
- Fixed bug in technique mapping queries (elimates some spurious/redundant mappings) in backend.
- Fix mispecified inverseOf relation on :accessses property which caused reasoning errors. (#88)
- Fix version data properties, and broken URLs on some has-link values. (#90)


## Version - 0.11.0-BETA-1 - 2022-10-31

- Added new large section of 'supporting' defensive techniques under tactic Model. (#12)
- Added semantic mappings to NIST 800-53 Rev 5 and DISA CCI (Common Common Control Index). (#68)
- Added large number of new artifact definitions for offensive and defensive techniques. (#67)
- Added a script to automatically create ontology additions for STIX2 based ATT&CK updates and update to ATT&CK V11. (#60)
- Update robot.jar URL. (#57)
- Fix label kerberos ticket. (#53)

## Version - 0.10.1-BETA-1 - 2022-06-13

- Ontology now supports docker builds, thanks @ioggstream. (#5)
- Ontology has Github CI builds, thanks @ioggstream. (#7)
- Ability to load ontology build into blazegraph with make target. (#20)
- Added more detail on key pinning and updated references. (#23)
- Fixed relationship on File Encryption. (#13)
- New reference for D3-PCA. (#18)
- Updated d3f:BiometricAuthentication authenticate UserAccount. (#14)
- New technique D3-NTF, Network Traffic Filtering. (#26)
- Updated Jena testing library. (#31)
- Reviewed and modified Credential Access Technique, Brute Force, and Brute Force subclasses to indicate more precisely the main digital artifacts being accessed (here tested by some means of trial and error.) Result with query from D3-SPP now results in new matches the the password-specific classes under Brute Force. (#30)
- Added grounding references to D3-RRDD Reverse Resolution Domain Denylisting; now it will not be filtered in the D3FEND matrix presentation. (#33)
- Added full pre-commit checks for code linting, syntax checking, and other hooks, thanks @ioggstream. (#35)
- Added Lure as synonym for Decoy Object. (#47)
- New reference for D3-RFS. (#46)
- Corrected definition on D3-FAPA. (#41)
- Changed relation on T1114.001 to 'reads' vs 'accesses'. (#17)
- Additional reference for D3-SPP. (#39)
- Defined additional artifact on D3-IOPR. (#48)
- Fixed capitalization issue on Kerberos Ticket digital artifact. (#51)

## Version - 0.10.0-BETA-2 - 2022-01-31

- Refactored any "create -> Process" relationships to "invokes -> Create Process" where "Create Process" is a type of system call.
- ATT&CK V10 included and characterized with Digital Artifacts.
- Refactored object property relationships for future inference support.
- New Defensive Techniques:
  - Application Configuration Hardening
  - Domain Trust Policy
  - User Account Permissions
  - File Encryption
  - System Configuration Permissions
  - Local Account Monitoring
  - Domain Account Monitoring
  - Peripheral Firmware Verification
  - System Firmware Verification
  - IO Port Restriction
  - System Call Filtering
  - Credential Transmission Scoping

## Version - 0.9.3-BETA-1 - 2021-07-09

- Process Spawn Analysis kb-article inaccuracy addressed regarding a discussion of threads.
- Removed overly-strong assertion in Homoglyph Detection technique.
- Fixed identifier for IPC Traffic Analysis to "D3-IPCTA".

## Version - 0.9.2-BETA-3 - 2021-06-22

- Many new countermeasure techniques.
- D3FEND Techniques now have acronym based identifiers.
- Major clean up of data properties and annotation properties.
- Many new offensive technique to digital artifact mappings.
- Defintions on almost all classes and puns, data, objecti, and annotation properties.
- Fixed latent issue from incorporating ATT&CK subtechniques, removed old parent classes from some ATT&CK techniques to fix display on knowledge base.
- Launchd vs Launch Daemon data entry error corrected.
- Ontology version is now depicted on d3f:D3FENDThing as owl:versionInfo.
- Experimental firmware taxonomy.
- Experimental sensor taxonomy.
