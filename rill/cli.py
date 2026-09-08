"""The command line: three verbs, no ceremony."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rill")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser(
        "witnesses", help="every testimony in full"
    )
    commands.add_parser(
        "check", help="exit nonzero if any witness is broken"
    )
    commands.add_parser(
        "summary", help="one line: witnesses and broken count"
    )
    arguments = parser.parse_args(argv)
    from rill.witnesses import registry

    if arguments.command == "witnesses":
        for testimony in registry.all_testimony():
            print(testimony.detail())
        return 0
    if arguments.command == "check":
        failing = registry.broken()
        if failing:
            print(
                f"{len(failing)} broken witness(es): "
                + ", ".join(failing)
            )
            return 1
        print("all witnesses hold")
        return 0
    if arguments.command == "summary":
        testimonies = registry.all_testimony()
        failing = sum(
            1 for testimony in testimonies if not testimony.holds
        )
        print(f"{len(testimonies)} witnesses ({failing} broken)")
        return 1 if failing else 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
