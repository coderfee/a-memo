"""memo CLI 入口"""
import argparse
import sys

from . import connect


def _get_version():
    try:
        from importlib.metadata import version
        return version("memo")
    except Exception:
        return "0.1.0"


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


COMMANDS = [
    "init",
    "reset",
    "add",
    "update",
    "delete",
    "list",
    "search",
    "review",
    "tag",
    "tags",
    "link",
    "unlink",
    "links",
    "rebuild-fts",
    "image",
    "flomo-import",
]

_MOD_ALIASES = {
    "rebuild-fts": "rebuild_fts",
    "flomo-import": "flomo_import",
}

_command_modules = {}


def _load(name):
    mod_name = _MOD_ALIASES.get(name, name)
    if mod_name not in _command_modules:
        try:
            mod = __import__(f"memo.commands.{mod_name}", fromlist=["add_parser"])
            _command_modules[mod_name] = mod
        except ImportError:
            _command_modules[mod_name] = None
    return _command_modules.get(mod_name)


def _levenshtein(a, b):
    """计算两个字符串之间的编辑距离"""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)

    previous_row = range(len(b) + 1)
    for i, ca in enumerate(a):
        current_row = [i + 1]
        for j, cb in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (ca != cb)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _suggest(cmd):
    """找到最相似的命令"""
    candidates = COMMANDS + list(_MOD_ALIASES.keys())
    best, best_dist = None, float("inf")
    for c in candidates:
        d = _levenshtein(cmd, c)
        if d < best_dist:
            best, best_dist = c, d
    return best, best_dist


def _print_help_and_exit():
    print("memoi — lightweight memo CLI for AI agents")
    print()
    print("USAGE:")
    print("    memoi <command> [options]")
    print()
    print("COMMANDS:")
    print("    init           initialize database")
    print("    reset          reset data directory")
    print("    add            add memo")
    print("    list           list memos")
    print("    search         search memos")
    print("    review         review memos")
    print("    update         update memo")
    print("    delete         delete memo")
    print("    tag            tag memo")
    print("    tags           list all tags")
    print("    link           link two memos")
    print("    unlink         unlink two memos")
    print("    links          view memo links")
    print("    image          generate share image")
    print("    rebuild-fts    rebuild search index")
    print("    flomo-import   import from flomo HTML")
    print()
    print("FLAGS:")
    print("    -h, --help     show help")
    print("    -v, --version  show version")
    print()
    print("more: memoi <command> --help")
    sys.exit(0)


def _print_version_and_exit():
    print(f"memoi {_get_version()}")
    sys.exit(0)


def main(argv=None):
    raw = argv if argv is not None else sys.argv[1:]

    if not raw or raw[0] in ("-h", "--help"):
        _print_help_and_exit()

    if raw[0] in ("-v", "--version"):
        _print_version_and_exit()

    parser = argparse.ArgumentParser(prog="memoi", add_help=False, exit_on_error=False)
    sub = parser.add_subparsers(dest="cmd", required=True)

    for cmd in COMMANDS:
        mod = _load(cmd)
        if mod:
            mod.add_parser(sub)

    try:
        args = parser.parse_args(raw)
    except SystemExit:
        # argparse --help exits, let it through
        raise
    except BaseException:
        # Catch invalid command and suggest similar one
        if raw and raw[0] not in COMMANDS:
            suggestion, dist = _suggest(raw[0])
            print(f"error: unknown command '{raw[0]}'", file=sys.stderr)
            if dist <= 3:
                print(f"       did you mean '{suggestion}'?", file=sys.stderr)
            print()
            _print_help_and_exit()
        raise

    conn = connect()
    try:
        args.func(conn, args)
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())