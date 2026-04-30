#!/usr/bin/env python3
"""Generate the Homebrew formula for a-memo release binaries."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

FORMULA = """class AMemo < Formula
  desc "Lightweight memo CLI tool with SQLite + FTS5"
  homepage "https://github.com/coderfee/a-memo"
  version "{version}"
  license "MIT"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/coderfee/a-memo/releases/download/v{version}/memo-macos-arm64.tar.gz"
      sha256 "{arm64_sha256}"
    else
      url "https://github.com/coderfee/a-memo/releases/download/v{version}/memo-macos-x86_64.tar.gz"
      sha256 "{x86_64_sha256}"
    end
  end

  def install
    bin.install "memo"
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
    parser.add_argument("--arm64", help="Path to memo-macos-arm64.tar.gz.")
    parser.add_argument("--x86-64", dest="x86_64", help="Path to memo-macos-x86_64.tar.gz.")
    parser.add_argument("--arm64-sha256", help="Checksum for memo-macos-arm64.tar.gz.")
    parser.add_argument(
        "--x86-64-sha256",
        dest="x86_64_sha256",
        help="Checksum for memo-macos-x86_64.tar.gz.",
    )
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
        arm64_sha256 = checksum(args.arm64_sha256, args.arm64, "arm64")
        x86_64_sha256 = checksum(args.x86_64_sha256, args.x86_64, "x86-64")
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        FORMULA.format(
            version=version,
            arm64_sha256=arm64_sha256,
            x86_64_sha256=x86_64_sha256,
        ),
        encoding="utf-8",
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
