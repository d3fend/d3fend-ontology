# D3FEND Change Log

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
