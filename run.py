"""
Ana Çalıştırıcı (Dispatcher)
-----------------------------
Config JSON dosyasını okur ve ilgili iş paketini (WP) çalıştırır.
Kullanım: python run.py --config config/<config_dosyasi>.json

İş paketleri (job değeri):
  w0_smoke          → WP0 smoke test
  w1_naive_sweep    → WP1 naive sweep
  w1_as_baseline    → WP1 AS baseline
  w1_compare        → WP1 karşılaştırma
  w2_synth          → WP2 sentetik veri üretimi
  w3_sanity         → WP3 ortam doğrulama
  w4_ppo            → WP4 PPO eğitimi
  w5_eval           → WP5 OOS değerlendirme
  w5_ablation_eta   → WP5 η ablasyon
  w5_ablation_skew  → WP5 skew penalty ablasyon
  w5_detector_compare → WP5 detector robustness
"""

import argparse
import json

from src.run_context import setup_run, finalize_run
from src.wp0.w0_smoke import wp0_smoke
from src.wp1.w1_naive_sweep import job_entry as w1_naive_sweep
from src.wp1.w1_as_baseline import job_entry as w1_as_baseline
from src.wp1.w1_compare import job_entry as w1_compare
from src.wp2.job_w2_synth import job_entry as w2_synth
from src.wp3.w3_sanity import job_entry as w3_sanity
from src.wp4.job_w4_ppo import job_entry as w4_ppo
from src.wp5.job_w5_eval import job_entry as w5_eval
from src.wp5.job_w5_ablation_eta import job_entry as w5_ablation_eta
from src.wp5.job_w5_ablation_skew import job_entry as w5_ablation_skew
from src.wp5.job_w5_detector_compare import job_entry as w5_detector_compare



def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=str, default="config/base.json")
    return p.parse_args()


def main():
    args = parse_args()
    ctx = setup_run(args.config)

    try:
        # setup_run bazı yapılarda cfg'yi ctx içine koyar; yoksa dosyadan okuruz
        if hasattr(ctx, "cfg") and isinstance(ctx.cfg, dict):
            cfg = ctx.cfg
        else:
            with open(args.config, "r", encoding="utf-8") as f:
                cfg = json.load(f)

        job = cfg.get("job", "w0_smoke")

        if job == "w0_smoke":
            wp0_smoke(ctx)  # WP0
        elif job == "w1_naive_sweep":
            w1_naive_sweep(cfg, ctx)  # WP1
        elif job == "w1_as_baseline":
            w1_as_baseline(cfg, ctx)
        elif job == "w1_compare":
            w1_compare(cfg, ctx)
        elif job == "w2_synth":
            w2_synth(cfg, ctx)
        elif job == "w3_sanity":
            w3_sanity(cfg, ctx)
        elif job == "w4_ppo":
            w4_ppo(cfg, ctx)
        elif job == "w5_eval":
            w5_eval(cfg, ctx)
        elif job == "w5_ablation_eta":
            w5_ablation_eta(cfg, ctx)
        elif job == "w5_ablation_skew":
            w5_ablation_skew(cfg, ctx)
        elif job == "w5_detector_compare":
            w5_detector_compare(cfg, ctx)
        elif job == "w55_audit":
            from src.wp5_5.job_w55_audit import run as run_w55_audit
            run_w55_audit(cfg, ctx)
        elif job == "w55_runtime":
            from src.wp5_5.job_w55_runtime import run as run_w55_runtime
            run_w55_runtime(cfg, ctx)
        elif job == "w55_calibration":
            from src.wp5_5.job_w55_calibration import run as run_w55_calibration
            run_w55_calibration(cfg, ctx)
        elif job == "w6_sweep_pilot":
            from src.wp6.job_w6_sweep_pilot import run as run_w6_sweep_pilot
            run_w6_sweep_pilot(cfg, ctx)
        else:
            raise ValueError(f"Unknown job: {job}")

        finalize_run(ctx, "success")

    except Exception as e:
        ctx.logger.exception("Run crashed.")
        finalize_run(ctx, "failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
