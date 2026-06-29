#For reading the terminal commands
import argparse
import json
import sys

from transformer.pipeline import run


def main(argv=None):
    p = argparse.ArgumentParser(description="Multi-source candidate data transformer")
    p.add_argument("--csv", help="recruiter CSV file")
    p.add_argument("--ats", help="ATS JSON file")
    p.add_argument("--notes", help="recruiter notes .txt file")
    p.add_argument("--config", help="custom-output config JSON (optional)")
    p.add_argument("--out", help="write JSON here instead of stdout")
    args = p.parse_args(argv)

    sources = {}
    if args.csv:
        sources["csv"] = args.csv
    if args.ats:
        sources["ats"] = args.ats
    if args.notes:
        sources["notes"] = args.notes
    if not sources:
        p.error("give at least one of --csv / --ats / --notes")

    config = None
    if args.config:
        with open(args.config, encoding="utf-8") as fh:
            config = json.load(fh)

    result = run(sources, config)
    text = json.dumps(result["profiles"], indent=2, ensure_ascii=False)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {len(result['profiles'])} profile(s) -> {args.out}", file=sys.stderr)
    else:
        print(text)

    for w in result["warnings"]:
        print(f"[warn] {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
