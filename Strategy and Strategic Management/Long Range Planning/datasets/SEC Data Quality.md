# SEC extraction quality and known limitations

The extraction intermediary returned source JSON for 26 of 30 firms. Four large companyfacts responses failed JSON parsing (META, CRM, V, COST). Do not silently fill missing records.

The narrow extract records five US GAAP measures where available: assets, revenue, net income, operating income and research and development expense. Bank financial reporting differs from non-financial firms; absent revenue or operating income cannot be treated as zero.

Selection was provisional: annual 10-K records with reported FY and 300–400-day durations, choosing latest filing date for a firm/metric/fiscal-year. This can mix originally reported and later restated facts and can misassign comparative fiscal-year values. A final audited panel must use filing accession, frame, period end, fiscal year, amendment policy, taxonomy mapping and financial-sector rules.

No statistical analysis or hypothesis test has been conducted.
