import json
import sqlite3
import sys
import time
from types import SimpleNamespace

import pytest
from memo import cli


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    path = tmp_path / "memo-data"
    monkeypatch.setenv("MEMO_DATA_DIR", str(path))
    monkeypatch.delenv("MEMO_DB_PATH", raising=False)
    return path


def run_cli(args, capsys):
    code = cli.main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def parse_json_output(output):
    return json.loads(output)


def db_path(data_dir):
    return data_dir / "memo.db"


def schema_version(data_dir):
    with sqlite3.connect(db_path(data_dir)) as conn:
        return conn.execute("PRAGMA user_version").fetchone()[0]


def make_old_memos(data_dir, count=2):
    created_at = time.time() - 8 * 86400
    with sqlite3.connect(db_path(data_dir)) as conn:
        for memo_id in range(1, count + 1):
            conn.execute(
                "UPDATE memos SET created_at=?, last_review_at=NULL WHERE id=?",
                (created_at - memo_id, memo_id),
            )


def test_help_version_unknown_command_and_invalid_argument(data_dir, capsys):
    with pytest.raises(SystemExit) as help_exit:
        cli.main(["--help"])
    assert help_exit.value.code == 0
    assert "memo <command>" in capsys.readouterr().out

    with pytest.raises(SystemExit) as version_exit:
        cli.main(["--version"])
    assert version_exit.value.code == 0
    assert capsys.readouterr().out.startswith("memo ")

    with pytest.raises(SystemExit) as invalid_arg_exit:
        cli.main(["list", "--limit", "nope"])
    assert invalid_arg_exit.value.code == 2

    with pytest.raises(SystemExit) as unknown_exit:
        cli.main(["llist"])
    assert unknown_exit.value.code == 2
    captured = capsys.readouterr()
    assert "unknown command 'llist'" in captured.err
    assert "did you mean 'list'" in captured.err


def test_init_add_list_search_tags_update_rebuild_and_delete(data_dir, capsys):
    code, out, err = run_cli(["init"], capsys)
    assert (code, out.strip(), err) == (0, "ready", "")
    assert schema_version(data_dir) == 1

    code, out, err = run_cli(["add", "hello", "world", "#Work/AI"], capsys)
    assert code == 0
    assert err == ""
    assert "created #1" in out
    assert "tags: #work/ai" in out

    code, out, _ = run_cli(["list", "#work"], capsys)
    rows = parse_json_output(out)
    assert [row["content"] for row in rows] == ["hello world"]
    assert rows[0]["tags"] == ["#work/ai"]

    code, out, _ = run_cli(["search", "hello"], capsys)
    rows = parse_json_output(out)
    assert code == 0
    assert rows[0]["id"] == 1

    code, out, _ = run_cli(["tags"], capsys)
    assert parse_json_output(out) == ["#work/ai"]

    code, out, err = run_cli(["update", "1", "updated", "memo"], capsys)
    assert code == 0
    assert err == ""
    assert "updated #1" in out
    assert "tags: #work/ai" in out

    code, out, _ = run_cli(["search", "updated"], capsys)
    assert parse_json_output(out)[0]["content"] == "updated memo"

    code, out, err = run_cli(["rebuild-fts"], capsys)
    assert (code, out.strip(), err) == (0, "fts rebuilt (1 memos indexed)", "")

    code, out, err = run_cli(["delete", "1"], capsys)
    assert (code, out.strip(), err) == (0, "deleted #1", "")

    code, out, _ = run_cli(["list"], capsys)
    assert parse_json_output(out) == []


def test_tag_link_links_unlink_and_related_errors(data_dir, capsys):
    run_cli(["add", "first", "#a"], capsys)
    run_cli(["add", "second", "#b"], capsys)

    code, out, err = run_cli(["tag", "1", "#extra"], capsys)
    assert code == 0
    assert err == ""
    assert "tagged #1: #a #extra" in out

    code, out, err = run_cli(
        ["link", "1", "2", "--type", "supports", "--note", "good link"], capsys
    )
    assert code == 0
    assert err == ""
    assert "linked #1 ↔ #2 (supports) · good link" in out

    code, out, _ = run_cli(["links", "1"], capsys)
    links = parse_json_output(out)
    assert links[0]["id"] == 2
    assert links[0]["relation_type"] == "supports"
    assert links[0]["note"] == "good link"

    code, out, err = run_cli(["unlink", "2", "1", "--type", "supports"], capsys)
    assert code == 0
    assert err == ""
    assert "unlinked #2 ↔ #1 (supports)" in out

    code, out, err = run_cli(["unlink", "1", "2", "--type", "supports"], capsys)
    assert code == 1
    assert out == ""
    assert "#1 ↔ #2 has no supports link" in err

    code, _, err = run_cli(["link", "1", "1"], capsys)
    assert code == 1
    assert "cannot link a memo to itself" in err

    code, _, err = run_cli(["links", "99"], capsys)
    assert code == 1
    assert "memo not found: #99" in err


def test_review_push_outputs_links_updates_counts_and_history(data_dir, capsys):
    run_cli(["add", "review one", "#r"], capsys)
    run_cli(["add", "review two", "#r"], capsys)
    run_cli(["link", "1", "2"], capsys)
    make_old_memos(data_dir, count=2)

    code, out, err = run_cli(["review", "--count", "2", "--push"], capsys)
    assert code == 0
    assert err == ""
    rows = parse_json_output(out)
    assert {row["id"] for row in rows} == {1, 2}
    assert any(row["links"] for row in rows)

    code, out, _ = run_cli(["list"], capsys)
    listed = parse_json_output(out)
    assert {row["review_count"] for row in listed} == {1}
    assert all("last_review_at" in row for row in listed)

    history_files = list((data_dir / "history").glob("*.md"))
    assert len(history_files) == 1
    history = history_files[0].read_text(encoding="utf-8")
    assert "#r review one" in history
    assert "#r review two" in history


def test_review_empty_when_no_eligible_memos(data_dir, capsys):
    run_cli(["add", "fresh"], capsys)

    code, out, err = run_cli(["review", "--count", "2"], capsys)
    assert (code, out.strip(), err) == (0, "[]", "")


def test_image_svg_and_png_subprocess_path(data_dir, tmp_path, monkeypatch, capsys):
    run_cli(["add", "shareable memo", "#img"], capsys)

    svg_path = tmp_path / "share.svg"
    code, out, err = run_cli(["image", "1", "--format", "svg", "--out", str(svg_path)], capsys)
    assert code == 0
    assert err == ""
    assert out.strip() == f"saved: {svg_path}"
    assert "<svg" in svg_path.read_text(encoding="utf-8")

    calls = []

    def fake_run(cmd, text, capture_output):
        calls.append(
            {
                "cmd": cmd,
                "text": text,
                "capture_output": capture_output,
            }
        )
        return SimpleNamespace(returncode=0, stdout="saved: fake.png\n", stderr="")

    import memo.commands.image as image_command

    monkeypatch.setattr(image_command.subprocess, "run", fake_run)
    png_path = tmp_path / "share.png"
    code, out, err = run_cli(["image", "1", "--format", "png", "--out", str(png_path)], capsys)
    assert code == 0
    assert err == ""
    assert out.strip() == "saved: fake.png"
    assert calls[0]["cmd"][:3] == [sys.executable, "-m", "memo.share_image"]
    assert calls[0]["text"] is True
    assert calls[0]["capture_output"] is True

    def fake_missing_playwright(cmd, text, capture_output):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="ModuleNotFoundError: No module named 'playwright'",
        )

    monkeypatch.setattr(image_command.subprocess, "run", fake_missing_playwright)
    code, _, err = run_cli(["image", "1", "--format", "png", "--out", str(png_path)], capsys)
    assert code == 1
    assert 'uv tool install --force "a-memo[png]"' in err

    def fake_missing_browser(cmd, text, capture_output):
        return SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Browser executable doesn't exist. Please run playwright install",
        )

    monkeypatch.setattr(image_command.subprocess, "run", fake_missing_browser)
    code, _, err = run_cli(["image", "1", "--format", "png", "--out", str(png_path)], capsys)
    assert code == 1
    assert "uv tool run playwright install chromium" in err

    code, _, err = run_cli(
        ["image", "1", "--format", "svg", "--out", str(tmp_path / "bad.png")], capsys
    )
    assert code == 1
    assert "svg output requires .svg extension" in err


def test_flomo_import_dry_run_success_and_failures(data_dir, tmp_path, capsys):
    html_path = tmp_path / "flomo.html"
    html_path.write_text(
        """
        <div class="memo">
          <div class="time">2024-01-02 03:04:05</div>
          <div class="content"><p>#flomo imported memo</p><p>second line</p></div>
        </div>
        <div class="memo">
          <div class="time">bad-date</div>
          <div class="content">will fail</div>
        </div>
        """,
        encoding="utf-8",
    )

    code, out, err = run_cli(["flomo-import", str(html_path), "--dry-run"], capsys)
    assert code == 0
    assert err == ""
    assert "parsed 2 memos" in out
    assert "imported 2, skipped 0, failed 0" in out

    code, out, err = run_cli(["flomo-import", str(html_path)], capsys)
    assert code == 1
    assert "imported 1, skipped 0, failed 1" in out
    assert "invalid datetime format: bad-date" in err

    code, out, _ = run_cli(["list", "#flomo"], capsys)
    rows = parse_json_output(out)
    assert len(rows) == 1
    assert rows[0]["content"] == "imported memo\nsecond line"

    code, out, err = run_cli(["flomo-import", str(tmp_path / "missing.html")], capsys)
    assert code == 1
    assert out == ""
    assert "file not found:" in err


def test_reset_force_deletes_data_directory(data_dir, capsys):
    run_cli(["add", "temporary"], capsys)
    assert db_path(data_dir).exists()

    code, out, err = run_cli(["reset", "--force"], capsys)
    assert code == 0
    assert err == ""
    assert "backup saved:" in out
    assert f"deleted: {data_dir}" in out
    assert not data_dir.exists()
    assert list(data_dir.parent.glob("memo-data-backup-*.db"))


def test_reset_and_backup_do_not_create_missing_database(data_dir, capsys):
    code, out, err = run_cli(["reset", "--force"], capsys)
    assert code == 0
    assert err == ""
    assert out.strip() == f"data dir not found: {data_dir}"
    assert not data_dir.exists()

    code, out, err = run_cli(["backup"], capsys)
    assert code == 1
    assert out == ""
    assert f"database not found: {db_path(data_dir)}" in err
    assert not data_dir.exists()


def test_explicit_memo_db_path(data_dir, tmp_path, monkeypatch, capsys):
    explicit_db = tmp_path / "custom" / "memo.db"
    explicit_db.parent.mkdir()
    monkeypatch.setenv("MEMO_DB_PATH", str(explicit_db))

    code, out, err = run_cli(["add", "custom db"], capsys)
    assert code == 0
    assert err == ""
    assert "created #1" in out
    assert explicit_db.exists()
    assert not db_path(data_dir).exists()


def test_backup_export_import_and_replace(data_dir, tmp_path, capsys):
    run_cli(["add", "alpha", "#one"], capsys)
    run_cli(["add", "beta", "#two"], capsys)
    run_cli(["link", "1", "2", "--note", "pair"], capsys)

    backup_path = tmp_path / "backup.db"
    code, out, err = run_cli(["backup", "--out", str(backup_path)], capsys)
    assert code == 0
    assert err == ""
    assert out.strip() == f"backup saved: {backup_path}"
    assert backup_path.exists()

    export_path = tmp_path / "export.json"
    code, out, err = run_cli(["export", "--out", str(export_path)], capsys)
    assert code == 0
    assert err == ""
    assert out.strip() == f"exported: {export_path}"
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["format"] == "a-memo-export"
    assert [memo["content"] for memo in payload["memos"]] == ["alpha", "beta"]
    assert payload["memo_links"][0]["note"] == "pair"

    run_cli(["delete", "1"], capsys)
    code, out, err = run_cli(["import", str(export_path), "--replace", "--no-backup"], capsys)
    assert code == 0
    assert err == ""
    assert out.strip() == "imported 2 memos"

    code, out, _ = run_cli(["list"], capsys)
    rows = parse_json_output(out)
    assert {row["id"] for row in rows} == {1, 2}

    code, out, _ = run_cli(["links", "1"], capsys)
    links = parse_json_output(out)
    assert links[0]["id"] == 2
    assert links[0]["note"] == "pair"


def test_import_append_remaps_links(data_dir, tmp_path, capsys):
    run_cli(["add", "existing"], capsys)

    export_path = tmp_path / "append.json"
    export_path.write_text(
        json.dumps(
            {
                "format": "a-memo-export",
                "schema_version": 1,
                "exported_at": time.time(),
                "memos": [
                    {
                        "id": 10,
                        "content": "imported one",
                        "tags": "[]",
                        "created_at": time.time(),
                        "updated_at": None,
                        "review_count": 0,
                        "last_review_at": None,
                        "source": "test",
                    },
                    {
                        "id": 20,
                        "content": "imported two",
                        "tags": "[]",
                        "created_at": time.time(),
                        "updated_at": None,
                        "review_count": 0,
                        "last_review_at": None,
                        "source": "test",
                    },
                ],
                "memo_links": [
                    {
                        "id": 99,
                        "from_memo_id": 10,
                        "to_memo_id": 20,
                        "relation_type": "related",
                        "note": "remapped",
                        "created_at": time.time(),
                        "source": "test",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    code, out, err = run_cli(["import", str(export_path)], capsys)
    assert code == 0
    assert err == ""
    assert out.strip() == "imported 2 memos"

    code, out, _ = run_cli(["search", "imported"], capsys)
    rows = parse_json_output(out)
    imported_ids = {row["id"] for row in rows}
    assert imported_ids == {2, 3}

    code, out, _ = run_cli(["links", "2"], capsys)
    links = parse_json_output(out)
    assert links[0]["id"] == 3
    assert links[0]["note"] == "remapped"


def test_legacy_database_migrates_to_current_schema(data_dir, capsys):
    data_dir.mkdir()
    with sqlite3.connect(db_path(data_dir)) as conn:
        conn.executescript(
            """
            CREATE TABLE memos (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              content TEXT NOT NULL,
              tags TEXT,
              created_at REAL NOT NULL,
              updated_at REAL,
              review_count INTEGER DEFAULT 0,
              last_review_at REAL,
              source TEXT DEFAULT 'cli'
            );
            CREATE TABLE memo_links (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              from_memo_id INTEGER NOT NULL,
              to_memo_id INTEGER NOT NULL,
              relation_type TEXT DEFAULT 'related',
              note TEXT,
              created_at REAL NOT NULL,
              source TEXT DEFAULT 'agent',
              UNIQUE(from_memo_id, to_memo_id, relation_type)
            );
            INSERT INTO memos (content, tags, created_at, source)
            VALUES ('legacy memo', '[]', 1, 'test');
            """
        )

    code, out, err = run_cli(["search", "legacy"], capsys)
    assert code == 0
    assert err == ""
    rows = parse_json_output(out)
    assert rows[0]["content"] == "legacy memo"
    assert schema_version(data_dir) == 1


def test_import_rejects_bad_payload(data_dir, tmp_path, capsys):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{}", encoding="utf-8")

    code, out, err = run_cli(["import", str(bad_path)], capsys)
    assert code == 1
    assert out == ""
    assert "unsupported import format" in err
