"""Declarations and appendices (proofs, pseudocode, reproducibility)."""


def declarations(N):
    B = []
    h1 = lambda t: B.append({"type": "h1", "text": t})
    p = lambda t: B.append({"type": "p", "text": t})
    h1("Author Contributions")
    p("Conceptualisation, methodology, software, validation, formal analysis, investigation, data curation, writing (original draft and review and editing) and visualisation: I.E. The author has read and agreed to the published version of the manuscript.")
    h1("Funding")
    p("This research received no external funding.")
    h1("Institutional Review Board Statement")
    p("Not applicable. The study used public, licensed industrial and testbed datasets that contain no personal data.")
    h1("Informed Consent Statement")
    p("Not applicable.")
    h1("Data Availability Statement")
    p("All committed data are public and openly licensed: AI4I 2020 (doi:10.24432/C5HS5C), SECOM (doi:10.24432/C54305), Steel Plates Faults (doi:10.24432/C5J88N), Combined Cycle Power Plant (doi:10.24432/C5002N), Gas Turbine CO and NOx Emissions (doi:10.24432/C5WC95) and RT-IoT2022 (doi:10.24432/C5P338) under CC BY 4.0; the Bosch CNC feature table derived from github.com/boschresearch/CNC_Machining at commit d60581d (CC BY 4.0); and the HAI 21.03 window table derived from github.com/icsdataset/hai at commit 2a814ce (CC BY-SA 4.0). Derived tables, acquisition scripts, checksums, per-run outputs and the analysis workbook are available at github.com/Imomazin/research-projects in the folder Industry and Intelligent Systems/Industries/Privacy Trust and Intelligent Systems in Industry Six.")
    h1("Code Availability")
    p("The NumPy DP-FedAvg implementation, secure aggregation, private aggregate risk control, tests, frozen protocol, configuration and analysis scripts are in the same folder, subfolder Experiments/Private Risk Control. A GitHub Actions workflow runs the test suite and a two-round smoke run on every change.")
    h1("Use of Generative AI")
    p("The author used Claude (Anthropic) to assist with literature searching, software implementation, execution of the computational experiments, statistical analysis, figure preparation and drafting of the manuscript text. All study decisions, the frozen protocol, the verification of every reference against a bibliographic source and the final text were reviewed by the author, who takes full responsibility for the content. No generative AI system is listed as an author.")
    h1("Acknowledgments")
    p("The author thanks the creators of the AI4I, SECOM, Steel Plates Faults, Combined Cycle Power Plant, Gas Turbine Emissions, RT-IoT2022, Bosch CNC Machining and HAI datasets for making their data public.")
    h1("Conflicts of Interest")
    p("The author declares no conflicts of interest.")
    return B


def appendices(N):
    B = []
    h1 = lambda t: B.append({"type": "h1", "text": t})
    p = lambda t: B.append({"type": "p", "text": t})
    eq = lambda t: B.append({"type": "eq", "text": t})
    h1("Appendix A. Proofs")
    p("**Proof of Proposition 1.** Fix the grid and let R~j~ = R(b~j~), which is non-decreasing in j. If R~j~ ≤ α~miss~ for every j there is nothing to prove. Otherwise let j∗ be the smallest index with R~j∗~ > α~miss~; j∗ depends only on the population and the grid. The scan admits a bin beyond j∗ − 1 only if it rejects at j∗, that is, only if p~j∗~ ≤ δ~test~. Condition on the calibration labels, so that the number of positives n~1~ is fixed and their scores are independent draws from the class-conditional law. The exact count of positives below b~j∗~ is M ∼ Bin(n~1~, R~j∗~) and the released statistic is m̃ = M + Z with Z ∼ Skellam(j∗μ, j∗μ) independent of M, because the noisy cumulative count is a sum of j∗ independent per-bin Skellam terms. Define the function")
    eq("F~n~(m) = P( Bin(n, α~miss~) + Z ≤ m ).")
    p("Since Bin(n~1~, R~j∗~) is stochastically larger than Bin(n~1~, α~miss~), P(F~n1~(m̃) ≤ u) ≤ u for every u, so F~n1~(m̃) is a valid p-value. The server uses n⁻ = Ñ~1~ − q in place of n~1~, where q is the 1 − δ~count~ quantile of Skellam(Bμ, Bμ) and Ñ~1~ = n~1~ + Z' with Z' ∼ Skellam(Bμ, Bμ). On the event E = {n⁻ ≤ n~1~}, which has probability at least 1 − δ~count~, F~n⁻~(m) ≥ F~n1~(m) for every m because Bin(n⁻, α) is stochastically smaller than Bin(n~1~, α). Therefore")
    eq("P( p~j∗~ ≤ δ~test~ ) ≤ P( F~n1~(m̃) ≤ δ~test~ ) + P(E^c^) ≤ δ~test~ + δ~count~.")
    p("The argument does not require Z and Z' to be independent. The same steps apply to the false-alarm scan, which admits bins from the top of the negative histogram, and a union bound over the two scans gives joint validity with probability at least 1 − 2(δ~test~ + δ~count~). The guarantee concerns the population risk conditional on the calibration sample and therefore holds for future records exchangeable with the calibration records; it says nothing about records from a shifted distribution. The selective-classification and interval scans are the same argument with risk events \"wrong and accepted\" and \"absolute residual at or above the half-width\", whose counts are binomial in the total number of calibration records. ∎")
    p("**Proof of Proposition 2.** Let D be a dataset and D' = D ∪ {x}. Roles are assigned by independent coin flips, so the roles of all records other than x have the same distribution under D and D', and x is a training record with probability π and a calibration record otherwise. Write M = (M~T~(D~T~), M~C~(D~C~, M~T~(D~T~))) for the release. Conditional on x being a training record, M~C~ depends on x only through the released model, so by post-processing P(M(D') ∈ S) ≤ exp(ε~T~) P(M(D) ∈ S) + δ. Conditional on x being a calibration record, M~T~ has the same output distribution under D and D', and for every fixed model M~C~ is (ε~C~, δ) differentially private in its calibration input, so P(M(D') ∈ S) ≤ exp(ε~C~) P(M(D) ∈ S) + δ. Averaging over the role of x gives P(M(D') ∈ S) ≤ exp(max(ε~T~, ε~C~)) P(M(D) ∈ S) + δ, and the reverse inequality follows identically. The per-client DP-SGD guarantee applies to each record of that client because each record belongs to exactly one client and the aggregate model is a post-processing of the client outputs. The Skellam histogram release changes exactly one coordinate by one under add-or-remove adjacency, so its privacy profile equals that of the scalar shift, which we evaluate exactly by summing the hockey-stick divergence over the integer support. ∎")
    p("**Proof of Proposition 3.** The scan admits the first bin only if F~n⁻~(m̃~1~) ≤ δ~test~, and F is non-decreasing in m. Without noise the most favourable observation is zero misses, F~n~(0) = (1 − α)^n^, so certification requires n ≥ ln δ~test~ / ln(1 − α), which is 30.6 for δ~test~ = 0.04 and α = 0.10. With noise a negative noise draw can occasionally admit the first bin with fewer events, so we report the smallest n at which a noisy count of zero is admitted at the lower count bound. This is the floor in the typical case and it is evaluated exactly. ∎")
    h1("Appendix B. Algorithms")
    B.append({"type": "code", "lines": [
        "Algorithm 1  DP-FedAvg client update (client k, round r)",
        "  input: global parameters w, local records (x_i, y_i), i = 1..n_k; batch B; rate q = B / n_k",
        "  for each local step:",
        "      draw S by including each record independently with probability q",
        "      for i in S: g_i = gradient of loss at (x_i, y_i); c_i = min(1, C / ||g_i||)",
        "      g = (sum_i c_i g_i + N(0, sigma_k^2 C^2 I)) / (q n_k);  v = beta v + g;  w = w - eta v",
        "  return w   (sigma_k chosen so the RDP accountant reports epsilon_T after all steps)",
        "",
        "Algorithm 2  Private aggregate risk control (binary detection)",
        "  input: shared model s(.), fixed edges b_0 < ... < b_B, targets alpha_miss, alpha_fa,",
        "         delta_test, delta_count, total Skellam parameter mu (exact profile gives epsilon_C)",
        "  each client k: h_k^+ = histogram of s(x) over calibration positives; h_k^- over negatives",
        "                 add Skellam(mu/K, mu/K) to every bin; mask with pairwise ChaCha20 masks",
        "  server: H^+ = secure sum of h_k^+;  H^- = secure sum of h_k^-",
        "          n1 = sum(H^+) - q(1 - delta_count; Skellam(B mu, B mu)); n0 likewise",
        "          j_low = 0; for j = 1..B: m = sum_{i<=j} H^+_i",
        "              if P(Bin(n1, alpha_miss) + Skellam(j mu, j mu) <= m) <= delta_test: j_low = j",
        "              else break",
        "          j_high = 0; for j = 1..B: m = sum of the top j bins of H^-",
        "              if P(Bin(n0, alpha_fa) + Skellam(j mu, j mu) <= m) <= delta_test: j_high = j",
        "              else break",
        "          t_low = b_{j_low} (or -inf); t_high = b_{B - j_high} (or +inf)",
        "  deploy: s < t_low -> automatic pass; s >= t_high -> automatic alarm; otherwise escalate",
    ]})
    p("Complexity. Each client spends one forward pass per calibration record and O(B) work to histogram and mask; communication is 2B 32-bit integers per client plus 32-byte public keys. The server evaluates at most 2B convolutions of length n + 1, each costing O(n). For the largest task (RT-IoT2022) this took well under a second per policy on one core.")
    h1("Appendix F. Reproducibility")
    p("To reproduce: clone the repository, install Experiments/Private Risk Control/Requirements.txt, run Data Collection/Acquire External Industrial Sources.py with a target outside the repository if the Bosch and HAI tables are to be rebuilt, then run, from Experiments/Private Risk Control, the commands \"python Run Confirmatory Study.py main --datasets <task> --seeds 1 2 3 4 5 6 7 8 9 10\", the sensitivity and reconstruction stages, \"python Validate Risk Guarantee.py\", \"python Compute Evidence Floor.py\", \"python Analyse Results.py\", \"python Make Figures.py\" and \"python Build Workbook.py\". Tests run with \"python Test Private Risk Control.py -v\" and cover data integrity, leakage of targets and groups, role disjointness, train-only scaling, gradient correctness, per-example clipping, noise scale, privacy calibration against the accountant and the exact Skellam profile, secure-aggregation correctness and failure under dropout, risk-control p-value validity and a Monte Carlo check of the guarantee.")
    return B
