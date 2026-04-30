# Homebrew Formula

`scripts/homebrew_formula.py` generates the `a-memo` Formula from release tarballs.

Local generation:

```bash
python3 scripts/homebrew_formula.py \
  --version 1.5.0 \
  --arm64 memo-macos-arm64.tar.gz \
  --x86-64 memo-macos-x86_64.tar.gz
```

The generated file is written to `packaging/homebrew/a-memo.rb`.

Release automation updates `coderfee/homebrew-tap` when `HOMEBREW_TAP_TOKEN` is configured in GitHub Actions secrets. The token needs write access to `coderfee/homebrew-tap`.
