# Annual gas turbine emissions dataset

Original UCI repository: https://archive.ics.uci.edu/dataset/551

Dataset DOI: 10.24432/C5WC95. Licence: CC BY 4.0.

Source data: 36,733 observed hourly readings from a single gas turbine in Turkey, collected during five years (2011–2015). The original year-specific CSV files preserve ordering within the years, but there are no cross-organisation client identifiers. The paper must not claim these data come from different factories.

The acquisition code fetches the source ZIP from UCI, validates its expected 11-column numeric schema, verifies the total row count and retains original CSV byte content in five files whose names use words. It records the original year and filename in the provenance audit with SHA-256 digests.

Recommended task: forecast NOx or CO emissions from the nine non-emissions sensor fields using forward-year validation. Never include the emissions target itself as a feature, or describe a random split as temporal generalisation. A federated experiment could simulate clients defined by year; these are NOT real autonomous industrial participants.

The acquisition script and GitHub workflow may be rerun to reverify provenance. The complete observations are committed only after automated schema, numerical-field and total-row-count checks have passed.
