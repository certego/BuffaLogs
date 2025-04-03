---
name: Feature - New alerting type
about: Suggest a new alerting type for this project
title: "[FEATURE] Adding <alerting_name> alerting type"
labels: alerting, backend, feature
assignees: ''

---

[FEATURE]: Adding <alerting_name> alerting type

**Why should this alerting type be integrated into BuffaLogs?**

< Explain the importance and benefits of integrating this alerting type into BuffaLogs. Describe how it enhances functionality, improves data coverage, or addresses a specific need. >

**Additional Information**

< If known, provide any extra details that might be useful for development, such as specific data formats, API references, or known challenges. >

**Questions or Concerns for Development**

< If present (otherwise delete this section) - list any uncertainties, technical doubts, or potential blockers that should be addressed before or during implementation. >

## Development Guidelines

* Branch Name: feature/add_<alerting_name>

* File to Create: Implement a new alerting file in the `buffalogs/impossible_travel/alerting` directory, naming it `<alerting_name>_alerting.py`

* This file must implement the abstract method defined in base_alerting.py.

* Update Enum and Factory: Add the new source to the `BaseAlerting.SupportedAlerters` Enum class.

* Update the `AlertFactory.get_alert_class` function to include the new alerting source.

* Testing: Create tests in the `buffalogs/impossible_travel/tests/` folder, naming it `test_alert_<alerting_name>.py`

* Documentation: Create a documentation file in the `docs/laerting` directory, naming it `<alerting_name>.md`
Include there also relevant screenshots showcasing the ingestion source in action.
