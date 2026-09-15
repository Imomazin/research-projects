# P3 Dataset Manifest

## 1. Criteo Attribution Modeling for Bidding Dataset

**Role:** primary real-world journey/attribution benchmark  
**Official source:** https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/  
**Scale:** 16.5M impressions, about 45K conversions and 700 campaigns; user, campaign, click, conversion, attribution, cost and timing fields support reconstruction of exposure histories  
**Licence:** Criteo page states CC BY-NC-SA 4.0 terms; comply with attribution, non-commercial and share-alike conditions  
**Use in P3:** compare heuristic Orbit attribution with causal/counterfactual estimates and evaluate downstream bidding/budget decisions  
**Repository policy:** do not commit the 623MB compressed raw dataset; retain source, checksum, filtering rules and derived non-identifying aggregates  
**Status:** source identified, acquisition pending

## 2. Criteo Uplift Modeling Dataset, unbiased release

**Role:** randomised causal validation benchmark  
**Official source:** https://ailab.criteo.com/criteo-uplift-prediction-dataset/  
**Scale:** 13,979,592 rows in the unbiased release with treatment indicator plus visit and conversion labels  
**Design:** assembled from incrementality tests in which part of the population was randomly prevented from advertising treatment  
**Use in P3:** validate treatment-effect/uplift components against randomised treatment assignment and test policy-value metrics  
**Repository policy:** no raw large file in GitHub; retain source, checksum and transformation specification  
**Status:** source identified, acquisition pending

## 3. UCI Online Retail

**Role:** independent digital-commerce transaction structure and external validity  
**Official source:** https://archive.ics.uci.edu/dataset/352/online%2Bretail  
**DOI:** 10.24432/C5BW33  
**Scale:** 541,909 transactions from a UK-based non-store retailer, with invoice, product, quantity, date, price, customer and country information  
**Licence:** CC BY 4.0  
**Causal limitation:** it has transactions but no randomised marketing exposure; it cannot by itself identify channel treatment effects  
**Use in P3:** revenue/customer structure, robustness and commerce realism, not standalone causal identification  
**Status:** directly retrievable through `ucimlrepo` and suitable for immediate ingestion

## 4. SkillHubs anonymised campaign data

**Role:** optional real-world commercial validation specified in the grant  
**Access:** private and subject to approval, de-identification and documented data-minimisation rules  
**Use in P3:** external commercial validation only after the public-data method is frozen  
**Status:** not yet ingested

## 5. Semi-synthetic causal journey benchmark

**Role:** known-ground-truth recovery test  
**Construction:** generate treatment and conversion processes calibrated to empirical journey distributions while retaining known causal effects, confounding strength and mediation structure  
**Use in P3:** measure causal effect recovery and attribution error where real observational data has no observable causal ground truth  
**Status:** generator to be implemented alongside Orbit causal engine
