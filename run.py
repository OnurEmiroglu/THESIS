import argparse
import json

from src.run_context import setup_run, finalize_run
from src.w0_smoke import wp0_smoke
from src.w1_naive_sweep import job_entry as w1_naive_sweep
from src.w1_as_baseline import job_entry as w1_as_baseline
from src.w1_compare import job_entry as w1_compare
from src.wp2.job_w2_synth import job_entry as w2_synth



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
        else:
            raise ValueError(f"Unknown job: {job}")

        finalize_run(ctx, "success")

    except Exception as e:
        ctx.logger.exception("Run crashed.")
        finalize_run(ctx, "failed", error=str(e))
        raise


if __name__ == "__main__":
    main()
