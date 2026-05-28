# Literature Review Positioning Note

Scope: thesis literature review and revised thesis draft direction only. This note is designed to keep the contribution defense-safe and bounded to the controlled synthetic high-frequency market-making environment.

## 1. Classical Market Making Literature

Classical market-making work provides the inventory-risk and quote-placement foundation for the thesis. Avellaneda-Stoikov-style models show how reservation prices and spreads can be adjusted for inventory, volatility, time horizon, and fill intensity assumptions. Later analytical work extends this inventory-control view and gives useful structure for explaining why volatility and inventory matter.

In the thesis, this literature supports the baseline and problem framing. It does not by itself answer the thesis question, because the thesis is not deriving a new closed-form quoting rule. Instead, it evaluates whether a PPO policy benefits from an additional categorical volatility-regime label when a continuous realized-volatility proxy, `sigma_hat`, is already part of the observation.

## 2. RL / DRL Market Making Literature

RL and DRL market-making studies motivate learning quote placement from simulated or data-driven environments rather than relying only on analytical approximations. This literature is directly relevant because it studies learned policies, state representations, inventory penalties, and robustness of market-making behavior.

The thesis should position itself as narrower than general RL market making. It does not claim to introduce the best market-making RL algorithm. Its contribution is an incremental signal-representation test inside a controlled synthetic HFMM setup: explicit categorical regime labels do not improve performance once `sigma_hat` is already observed.

## 3. Volatility Regimes and Non-Stationarity

Volatility regimes and non-stationarity remain economically meaningful. Regime labels can be useful when they summarize latent market conditions, reduce noise, or expose state information that the policy would otherwise miss.

This thesis does not claim that volatility regimes are irrelevant. It asks a narrower incremental-value question: once a continuous realized-volatility proxy `sigma_hat` is already available to the PPO policy, does an additional categorical volatility-regime label provide robust incremental value?

The thesis evidence supports the answer: in the tested synthetic high-frequency market-making environment, explicit categorical regime labels do not provide a reliable performance improvement beyond the continuous volatility signal.

## 4. Signal/State Representation and Redundancy

The central interpretation is signal redundancy. If `sigma_hat` already carries the volatility information needed for quote adaptation, a categorical label derived from related volatility information may add little or no usable incremental state information.

Defense-safe phrasing is: the results are consistent with signal redundancy. The thesis should avoid claiming a proven internal mechanism. The experiments show observed performance patterns under specified synthetic conditions; they do not prove exactly how the neural policy internally uses or ignores each observation channel.

## 5. Equivalence Testing / TOST

Equivalence testing is useful because the thesis does not merely want to say "no statistically significant improvement was found." TOST-style framing helps express whether the observed aware-versus-blind or combined-versus-sigma-only differences are small enough to be considered practically equivalent under a predefined margin.

This supports a careful conclusion: no robust incremental value in the tested synthetic environment. It should not be rewritten as proof that labels contain zero information.

## 6. Exact Thesis Gap

Prior literature establishes that:

- inventory and volatility matter for market-making quote control;
- RL and DRL can learn market-making policies;
- signals and non-stationary state information can matter in adaptive trading systems.

The exact thesis gap is narrower:

When a PPO market-making policy already observes a continuous realized-volatility estimate, does adding an explicit categorical volatility-regime label improve out-of-sample performance in a controlled synthetic HFMM environment?

The thesis answer is:

In the tested synthetic environment, explicit labels do not improve performance once `sigma_hat` is already observed. This is consistent with signal redundancy and does not imply volatility regimes are irrelevant.

## 7. Defense-Safe Wording

Use:

- "no robust incremental value in the tested synthetic environment"
- "consistent with signal redundancy"
- "explicit labels do not improve performance once `sigma_hat` is already observed"
- "this does not imply volatility regimes are irrelevant"
- "the evidence is from a controlled synthetic HFMM setting"
- "the thesis evaluates incremental signal value, not live-trading viability"

## 8. Claims To Avoid

Avoid:

- "regimes are useless"
- "labels contain zero information"
- "we proved the internal mechanism"
- "categorical interference is conclusively proven"
- "works in markets outside the controlled thesis environment"
- "live trading claim"
- "the result generalizes to all market-making environments"


