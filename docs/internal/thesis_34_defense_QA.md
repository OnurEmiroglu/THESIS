# thesis_34 Defense Q&A

Purpose: oral-defense preparation for thesis_34. This note is not manuscript
text and does not change any experiment, figure, protected CSV, or numerical
claim. Use it to answer reviewer-style questions while keeping the claim bounded
to the controlled synthetic HFMM environment.

Core thesis claim to preserve: explicit categorical volatility-regime labels do
not provide robust incremental value once `sigma_hat` is already observed by the
PPO policy in the tested controlled synthetic environment. The results are
consistent with signal redundancy plus mild categorical-channel degradation; no
internal PPO mechanism is proven.

## 1. Why no formal power analysis for TOST?

Short answer: the thesis uses TOST as an interpretable equivalence framework on
the frozen 20-seed experiments, not as a prospectively powered clinical-style
equivalence trial.

Defense answer: a formal power analysis would require a pre-specified smallest
effect size of interest, an assumed distribution of paired seed differences, and
a prospective sample-size plan. This project instead fixed a canonical
experiment budget and then reports paired tests, confidence intervals, TOST
results, and directional seed-level evidence together. The TOST results should
therefore be read as practical-equivalence evidence under explicit bounds, not
as the sole basis for the conclusion.

If pressed: the paper-version extension would be to pre-register the equivalence
bound, run a simulation-based power analysis over expected paired differences,
and then choose the seed count prospectively.

## 2. Why is regime separation fixed at sigma_mult = [0.6, 1.0, 1.8]?

Short answer: it is a canonical calibration chosen to create a clear but still
controlled low/medium/high volatility structure.

Defense answer: the regime multipliers are fixed so that the thesis can isolate
the signal-representation question: once the policy sees a continuous realized
volatility proxy, does adding the categorical label help? Varying the regime
separation would become a second experiment axis. The chosen calibration creates
visible volatility heterogeneity and nontrivial detector behavior while keeping
the market simulator simple enough for controlled comparisons.

Boundary: the thesis does not claim that this separation is universal or
optimal. A natural extension is a regime-separation sensitivity grid.

## 3. Why only mild misspecification?

Short answer: the mild misspecification check is a bounded robustness check, not
a full model-risk study.

Defense answer: stronger misspecification would require rethinking the simulator
calibration, training budget, and interpretation of each strategy. The thesis
uses mild regime-dependent execution changes to test whether the main signal
pattern immediately breaks when execution is not perfectly homogeneous. It does
not claim robustness to all market-model errors.

If pressed: a paper version should add a graded misspecification sweep, including
stronger regime-dependent arrival intensity, adverse-selection terms, queue
priority, and self-exciting flow.

## 4. Is the OOS protocol truly out-of-sample?

Short answer: yes, but in the temporal hold-out sense within the same synthetic
data-generating process.

Defense answer: the OOS protocol is a chronological 70/30 split. PPO trains on
the first segment and is evaluated on the later held-out segment. That controls
for same-path train/test leakage and gives a temporal generalization test inside
the synthetic simulator. It is not an out-of-distribution test across different
markets or fundamentally different data-generating processes.

Boundary: multiple seeds improve robustness to simulation randomness, but they
do not establish external market validity.

## 5. Why only PPO?

Short answer: PPO is used as a stable controlled testbed for a signal-design
question, not as a claim that PPO is the best market-making algorithm.

Defense answer: the central comparison is within PPO: `sigma_only`, `combined`,
`regime_only`, `oracle_full`, and `oracle_pure`. Holding the algorithm fixed
reduces confounding. Adding DQN, SAC, A2C, or custom architectures would shift
the thesis from signal representation into algorithm benchmarking.

If pressed: algorithm breadth is a paper-version extension. The first question
would be whether the same signal pattern persists under another policy class,
not whether PPO is globally optimal.

## 6. Why do sigma_only values differ across tables?

Short answer: the tables come from distinct frozen experiment batches and should
not be read as repeated estimates of one identical cell.

Defense answer: `sigma_only` appears in the five-variant ablation, the
regime-conditional eta check, the mild misspecification check, and the
signal-informativeness sweep. These runs can differ by config, condition,
training/evaluation batch, degradation setting, or experimental purpose. The
correct comparison is within each table or figure, using the paired design and
the stated frozen run provenance.

Useful phrasing: compare rows within a frozen experiment, not raw means across
different experiment families.

## 7. Why use sqrt(1/dt) in Sharpe-like?

Short answer: it is the project metric implemented in code: per-step PnL
standardized by step volatility and scaled by `sqrt(1 / dt)`.

Code definition: with `rets = diff(equity)`, the metric computes
`mean(rets) / std(rets, ddof=1) * sqrt(1 / dt)` when the standard deviation is
positive, otherwise `0.0`.

Defense answer: this is a simulator-scale risk-adjusted PnL metric. It is named
Sharpe-like because it resembles a Sharpe ratio but is not a market annualized
Sharpe ratio based on real calendar returns, financing, benchmark excess
returns, or live execution costs.

## 8. Does Appendix C support signal redundancy?

Short answer: Appendix C supports the interpretation, but it is not the primary
evidence.

Defense answer: Appendix C action diagnostics help show how policies behave
across regimes and can be read as post-hoc support for the signal-redundancy
interpretation. The main evidence remains the canonical OOS evaluation,
five-variant ablation, detector robustness, oracle-label comparisons,
reward-shaping and misspecification checks, and the signal-informativeness
sweep.

Boundary: Appendix C should not be presented as a mechanism proof. Action-level
diagnostics can be suggestive even when they do not identify the internal PPO
representation.

## 9. What recent literature is closest?

Short answer: the closest recent paper-version context is work on RL market
making under non-stationary LOB dynamics and richer event-based LOB simulation.

References to mention orally only, not as thesis_34 manuscript sources:

- Zimmer & Costa (2025), "Reinforcement Learning-Based Market Making as a
  Stochastic Control on Non-Stationary Limit Order Book Dynamics,"
  arXiv:2509.12456.
- Lalor & Swishchuk (2025), "Event-Based Limit Order Book Simulation under a
  Neural Hawkes Process: Application in Market-Making," Applied Mathematical
  Finance / arXiv:2502.17417.

How to frame them: these papers point toward the next research layer: richer
non-stationary dynamics and event-based/Hawkes-style simulators. thesis_34 is
more controlled and narrower; it asks whether a categorical regime channel adds
incremental value once `sigma_hat` is already present.

## 10. What is the first paper-version extension?

Short answer: move from a controlled synthetic regime simulator to a richer
event-based LOB setting while preserving the signal-representation question.

Recommended first extension:

1. Keep the thesis comparison structure: `sigma_only`, `combined`,
   `regime_only`, `oracle_full`, and `oracle_pure`.
2. Add a regime-separation and misspecification grid, including stronger
   execution heterogeneity.
3. Pre-specify the practical equivalence bound and run a seed-count/power
   analysis for TOST.
4. Test in a richer event-based or Hawkes-style LOB simulator before making any
   external-market claim.

Defense framing: the thesis is a clean first step showing that in the tested
controlled environment, categorical regime labels do not robustly improve PPO
once continuous volatility is observed. The paper extension should test whether
that pattern survives in richer market dynamics.
