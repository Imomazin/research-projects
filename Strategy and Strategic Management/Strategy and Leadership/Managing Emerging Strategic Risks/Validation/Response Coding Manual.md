# Coding manual for documented strategic response

Version for the revision, 25 October 2026. Written before the revised validation sample was coded.

## Purpose and unit

The unit of coding is a sentence-category pair: one sentence from Item 1 (Business) or Item 7 (Management's Discussion and Analysis) of a 10-K together with one of the nine risk categories (geopolitical, trade policy, regulatory change, cybersecurity, technological disruption, supply chain, climate and environment, macro-financial, pandemic). The coder decides whether the sentence documents an implemented organisational response to a threat in that category. Coders see the sentence, the category, the firm identifier and the fiscal year. Coders must not see the stratum or any rule-based label.

## Conceptual definitions

Risk recognition is the firm naming a threat that could affect its operations, costs, revenue or assets. Recognition alone involves no action and is never coded as a response.

Risk disclosure is the statement of a recognised threat in a public filing, normally in Item 1A, in language a reader can attribute to the firm. Disclosure is shaped by legal liability and by the Securities and Exchange Commission's materiality guidance, so it measures what the firm chooses to report rather than what it does.

Risk anticipation is a statement about how a threat is expected to develop or to affect the firm, with some indication of direction, timing or scale. A sentence such as "we expect tariffs on steel to raise our input costs in 2019" anticipates. It records no action.

Routine operational activity is an action the firm would take in the ordinary course of business whatever the threat: a standing currency or interest-rate hedging programme, standard purchase and supply contracts, scheduled information technology upgrades, ordinary capacity additions for growth, routine acquisitions with no stated risk purpose, compliance with an existing rule. Routine activity can reduce exposure, but the filing gives no evidence that it was undertaken because of the threat, so it does not qualify.

Reactive risk management is an action taken after a threat has materialised that contains or offsets its effect on the firm: cost reductions after demand fell in the pandemic, surcharges after tariffs were imposed, expedited freight during port congestion, incident response after a breach. It qualifies as an implemented response when the link to the threat is stated.

Proactive strategic adaptation is an action that changes the firm's exposure to a threat before, or independently of, a realised loss: qualifying second sources, relocating production, holding safety stock against expected shortages, redesigning products to use available components, investing in security architecture against a named threat. It qualifies when the link to the threat is stated.

Resource reconfiguration is the subset of reactive or proactive responses in which the firm adds, removes, moves or recombines assets, capacity, suppliers, products, people or systems. It is recorded separately because dynamic-capabilities theory treats reconfiguration as the final and most demanding step after sensing and seizing.

Evidence of implemented strategic response is a sentence that describes a reactive or proactive response that has been completed or is under way, by the firm, with an explicit or clearly implied link to a threat in the labelled category. This is the target concept of the measure.

## Coding fields

| Field | Values | Rule |
|---|---|---|
| category_relevant | 1 or 0 | 1 if the sentence concerns a threat in the labelled category to this firm. Word matches with another meaning are 0 (legal sanctions, the firm's own products as a supplier, customers' cybersecurity needs). |
| response_class | 0 to 4 | 0 no organisational action (risk statement, description of the business, results); 1 routine operational activity; 2 reactive risk management; 3 proactive strategic adaptation; 4 proposal, plan, aspiration or hypothetical. |
| threat_link | 1 or 0 | 1 if the sentence states, or the clause structure plainly implies, that the action addresses the labelled threat ("to reduce our dependence on suppliers in China", "in response to the tariffs"). An action that sits next to a risk word without a stated purpose is 0. |
| status | completed, ongoing, planned, hypothetical, not applicable | Completed or ongoing only when the text reports that the action happened or is happening. "We are implementing" is ongoing. "We plan to", "we intend", "we will", "we may" are planned or hypothetical. |
| reconfiguration | 1 or 0 | 1 if the response moves, adds, removes or recombines assets, capacity, suppliers, products, people or systems. |
| resource_commitment | 1 or 0 | 1 if a commitment of money, capacity, facilities, inventory, people or a contract is stated. |
| qualifies | 1 or 0 | 1 only if category_relevant = 1, response_class is 2 or 3, threat_link = 1 and status is completed or ongoing. |
| notes | text | Reason for any difficult decision. |

## Decision rules for common cases

Currency and interest-rate hedging. Standing programmes using forwards, swaps or options are routine operational activity (class 1) even when the sentence says the purpose is to reduce exposure, because the programmes run in every year and every firm with foreign operations has one. Code class 2 or 3 only when the hedge is a new action tied to a named event ("in response to the volatility following the referendum we extended our hedging horizon to 24 months").

Acquisitions. An acquisition is class 1 unless the sentence states a risk purpose ("we acquired our principal supplier of castings to secure supply"). Acquiring a company that sells cybersecurity or supply-chain products is a business decision about the product range and is not a response to the firm's own threat.

Supply contracts. Standard purchase or supply agreements are class 1. Long-term agreements, capacity reservations or prepayments that the sentence ties to shortages or to securing supply are class 2 or 3.

Technology investment. Investment in technology is a response only when the sentence ties it to the labelled threat (technological disruption to the firm's model, cyber threat, supply visibility). Growth investment in new products is class 1 or 0.

Cybersecurity measures. Completed security improvements tied to cyber threats qualify. Generic statements that the firm "maintains" security programmes are class 1 because they describe standing activity rather than a response. Products sold to customers are category_relevant = 0.

Business continuity. Implementing or activating continuity plans because of a named threat qualifies. A general statement that plans exist is class 1.

Geographic diversification and supply-chain restructuring. Moving production, sourcing or suppliers out of an exposed location, adding second sources, or redesigning networks qualifies when the sentence ties the move to the threat. Expansion into new markets for growth is class 1.

Strategic investment, capital allocation and operational reconfiguration. Plant closures, divestitures, cost programmes and capital reallocation qualify only when the sentence ties them to the labelled threat. Restructuring "to improve efficiency" is class 1.

Price actions. Surcharges and price increases that the sentence ties to tariffs, inflation or input-cost shocks are reactive responses (class 2).

Timing. The coder records what the sentence says happened. An action dated after the fiscal year of the filing cannot appear in it, except as a plan, which is class 4. When a sentence in a later filing reports an action from an earlier year, code the action as completed; the analysis uses the filing year.

Compound sentences. If any clause meets the qualifying conditions for the labelled category, code the pair as qualifying and record the clause in notes.

## Procedure for human coders

Two coders work independently from this manual and the blank coding sheet, without access to each other's codes, the rule-based labels or the strata. Each first codes the 20 training items in the training sheet and discusses disagreements with the lead author; the training items are excluded from agreement statistics. Each then codes the full sample. Agreement is reported as Cohen's kappa and Krippendorff's alpha for qualifies, response_class and threat_link, with raw agreement. Disagreements are then resolved by discussion, and the resolved label is the reference for precision and recall. Run Validation/compute agreement.py on the two completed sheets.

## Status

Human coding has not been carried out. The labels in Validation/Response Validation Reference Coding.csv were assigned by an AI assistant (Claude) applying this manual. They are a provisional reference that shows how the rules perform against the conceptual definitions; they are not independent human annotation and must not be reported as such.
