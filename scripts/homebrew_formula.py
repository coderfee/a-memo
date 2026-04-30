#!/usr/bin/env python3
"""Generate the Homebrew formula for the a-memo Python package."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

FORMULA = """class AMemo < Formula
  include Language::Python::Virtualenv

  desc "Lightweight memo CLI tool with SQLite + FTS5"
  homepage "https://github.com/coderfee/a-memo"
  url "https://github.com/coderfee/a-memo/releases/download/v{version}/a_memo-{version}.tar.gz"
  sha256 "{sdist_sha256}"
  version "{version}"
  license "MIT"

  depends_on "pillow"
  depends_on "python@3.13"

  def install
    virtualenv_install_with_resources using: "python3.13"
  end

  test do
    ENV["MEMO_DATA_DIR"] = testpath.to_s
    system "#{{bin}}/memo", "--version"
    system "#{{bin}}/memo", "add", "brew test #brew"
    assert_match "brew test", shell_output("#{{bin}}/memo list")
  end
end
"""


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[a-zA-Z0-9._-]+)?$")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate packaging/homebrew/a-memo.rb for a tagged release."
    )
    parser.add_argument("--version", required=True, help="Release version without leading v.")
    parser.add_argument("--sdist", help="Path to a_memo-VERSION.tar.gz.")
    parser.add_argument("--sdist-sha256", help="Checksum for a_memo-VERSION.tar.gz.")
    parser.add_argument(
        "--out",
        default="packaging/homebrew/a-memo.rb",
        help="Output formula path.",
    )
    return parser.parse_args()


def checksum(value: str | None, path: str | None, label: str) -> str:
    if value:
        if not SHA256_RE.match(value):
            raise ValueError(f"{label} sha256 must be 64 lowercase hex characters")
        return value
    if path:
        return file_sha256(Path(path))
    raise ValueError(f"provide either --{label} or --{label}-sha256")


def main() -> int:
    args = parse_args()
    version = args.version.removeprefix("v")
    if not VERSION_RE.match(version):
        print(f"invalid version: {args.version}", file=sys.stderr)
        return 2

    try:
        sdist_sha256 = checksum(args.sdist_sha256, args.sdist, "sdist")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        FORMULA.format(
            version=version,
            sdist_sha256=sdist_sha256,
        ),
        encoding="utf-8",
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
