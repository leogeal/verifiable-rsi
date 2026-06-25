"""Command-line interface for the SRSI harness.

Subcommands:

* ``run``          -- run the self-improvement loop on a domain and print an
                      honest report (findings with evidence levels, unsolved
                      instances, integrity violations caught).
* ``list-domains`` -- list available research domains.
* ``verify``       -- re-check a completed run's lineage hash chain and compare
                      the trusted-core fingerprint against the current code.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import available_domains, build_domain
from .engine.gates import SafetyConfig, SafetyGate
from .engine.improver import RecursiveImprover
from .engine.lineage import verify_chain
from .trusted.integrity import protected_fingerprint


def _cmd_run(args: argparse.Namespace) -> int:
    domain = build_domain(args.domain)
    gate = SafetyGate(SafetyConfig(max_overfit_gap=args.max_overfit_gap))
    improver = RecursiveImprover(
        domain,
        gate=gate,
        budget_steps=args.budget,
        holdout_frac=args.holdout_frac,
        seed=args.seed,
    )
    result = improver.run(iterations=args.iterations, out_dir=args.out)

    print("domain        :", result.domain)
    print("selection ids :", improver.selection_ids)
    print("held-out ids  :", improver.holdout_ids)
    print("protected core:", result.protected_fingerprint[:16])
    print()
    print("--- self-improvement trace ---")
    for record in result.records:
        if record.accepted:
            print(
                "gen {:>2}  PROMOTE  {:<28}  sel acc {:.3f}  held-out acc {:.3f}".format(
                    record.iteration,
                    str(record.change),
                    record.selection["accuracy"],
                    record.holdout["accuracy"],
                )
            )
        else:
            print("gen {:>2}  STOP     {}".format(record.iteration, record.reasons[0]))

    print()
    print("--- best strategy ---")
    print("params        :", json.dumps(result.best_genome.to_dict()["params"], sort_keys=True))
    print(
        "accuracy      : selection {:.3f}   held-out {:.3f}".format(
            result.best_selection.accuracy, result.best_holdout.accuracy
        )
    )
    print("evidence      :", json.dumps(result.evidence_breakdown, sort_keys=True))

    print()
    print("--- VERIFIED FINDINGS ({}) ---".format(len(result.findings)))
    for finding in result.findings:
        print("  [{}] {}".format(finding["evidence_label"], finding["statement"]))

    if result.unsolved:
        print()
        print("--- HONESTLY UNSOLVED ({}) ---".format(len(result.unsolved)))
        print("  " + ", ".join(result.unsolved))

    if result.integrity_events:
        print()
        print("--- INTEGRITY VIOLATIONS CAUGHT ({}) ---".format(len(result.integrity_events)))
        for event in result.integrity_events:
            print("  gen {}  {}  ->  {}".format(event["iteration"], event["change"], event["reason"]))

    print()
    print("counters      :", json.dumps(result.counters, sort_keys=True))
    print("stopped       :", result.stopped_reason)
    if args.out is not None:
        print("artifacts     :", args.out)
    return 0


def _cmd_list_domains(args: argparse.Namespace) -> int:
    for name in available_domains():
        print(name)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    summary = json.loads((args.run / "run_summary.json").read_text(encoding="utf-8"))
    chain_ok = verify_chain(summary["records"])
    recorded_fp = summary["protected_fingerprint"]
    current_fp = protected_fingerprint()
    print("lineage hash chain intact  :", chain_ok)
    print("protected fp (recorded)    :", recorded_fp[:16])
    print("protected fp (current code):", current_fp[:16])
    print("protected core unchanged   :", recorded_fp == current_fp)
    return 0 if (chain_ok and recorded_fp == current_fp) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="srsi",
        description="Sandboxed recursive self-improvement research harness.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the self-improvement loop on a domain")
    run.add_argument("--domain", choices=available_domains(), default="theorem")
    run.add_argument("--iterations", type=int, default=12)
    run.add_argument("--budget", type=int, default=300, help="step budget per instance")
    run.add_argument("--holdout-frac", type=float, default=0.4)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--max-overfit-gap", type=float, default=0.25)
    run.add_argument("--out", type=Path)
    run.set_defaults(func=_cmd_run)

    listd = sub.add_parser("list-domains", help="list available research domains")
    listd.set_defaults(func=_cmd_list_domains)

    verify = sub.add_parser("verify", help="re-check a completed run's audit trail")
    verify.add_argument("run", type=Path, help="a run output directory")
    verify.set_defaults(func=_cmd_verify)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
