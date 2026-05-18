# HFMM_REALDATA — Real-data extension of HFMM thesis

Branch: realdata-v1 (forked from thesis-v29-frozen)

**Important**: This branch deviates from the frozen thesis. The reproducibility chain
of thesis_29.pdf is unaffected (anchored at tag thesis-v29-frozen, commit 27c11bd).

**Status**: Phase 1A (data infra + sample validation). No model code yet.

## Methodology disclaimer (to be expanded in observation_mapping.md)
Real-data observation features are an empirical approximation layer; they are not
assumed information-equivalent to the synthetic environment's observation vector.
The "regime label redundancy" finding of thesis_29 is a formal result conditional
on the synthetic environment's identifiability properties. The real-data study
performs an empirical consistency check, not a formal extension of that result.

## Data immutability
Files under `data/raw/` are immutable after first write. All transformations
must write to `data/processed/`. Any need to re-download should produce a
new file (e.g., timestamped suffix), not an overwrite.
