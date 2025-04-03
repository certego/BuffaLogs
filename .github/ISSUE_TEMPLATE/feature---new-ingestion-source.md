---
name: Feature - New ingestion source
about: Suggest a new ingestion source for this project
title: "[FEATURE]: Integrating <source_name> ingestion source"
labels: backend, feature, ingestion
assignees: ''

---

**Why should this ingestion source be integrated into BuffaLogs?**

< Explain the importance and benefits of integrating this ingestion source into BuffaLogs. Describe how it enhances functionality, improves data coverage, or addresses a specific need. >

**Additional Information**

< If known, provide any extra details that might be useful for development, such as specific data formats, API references, or known challenges. >

**Questions or Concerns for Development**

< If present (otherwise delete this section) - list any uncertainties, technical doubts, or potential blockers that should be addressed before or during implementation. >

## Development Guidelines

* Branch Name: feature/add_<ingestion_source_name>

* Add configs for the ingestion source: into the `config/buffalogs/ingestion.json` file insert the settings and mapping fields for the ingestion source considered

* File to Create: Implement a new ingestion source file in the following directory, naming it `<ingestion_source_name>_ingestion.py` This file must implement the three abstract classes defined in base_ingestion.py.

* Update Enum and Factory: Add the new source to the SupportedIngestionSources Enum class and the `IngestionFactory.get_ingestion_class` function to include the new source.

* Testing: Create tests in the `buffalogs/impossible_travel/tests/` directory, naming it `test_<ingestion_source_name>_ingestion.py`

* Documentation: Create a documentation file in the `docs/ingestion/` directory, naming it `<ingestion_source_name>.md`
Include there also relevant screenshots showcasing the ingestion source in action.

Reference Implementation:
Check the existing implementation in `elasticsearch_ingestion.py` and its corresponding test `test_elasticsearch_ingestion.py` as a reference.
