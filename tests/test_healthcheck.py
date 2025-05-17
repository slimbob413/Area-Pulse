import sys
import json
import time
import pytest
from src import healthcheck

def run_healthcheck_with_state(state_dict, tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps(state_dict))
    # Monkeypatch open to use this file
    orig_open = open
    def fake_open(f, mode='r', *a, **k):
        if f == "state/state.json":
            return orig_open(state_file, mode)
        return orig_open(f, mode, *a, **k)
    return state_file, fake_open

def test_healthcheck_healthy(monkeypatch, tmp_path):
    now = time.time()
    state, fake_open = run_healthcheck_with_state({"last_run_timestamp": now}, tmp_path)
    monkeypatch.setattr("builtins.open", fake_open)
    exit_code = None
    def fake_exit(code):
        nonlocal exit_code
        raise SystemExit(code)
    monkeypatch.setattr(sys, "exit", fake_exit)
    try:
        healthcheck.main()
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 0

def test_healthcheck_stale(monkeypatch, tmp_path):
    old = time.time() - 4*3600
    state, fake_open = run_healthcheck_with_state({"last_run_timestamp": old}, tmp_path)
    monkeypatch.setattr("builtins.open", fake_open)
    exit_code = None
    def fake_exit(code):
        nonlocal exit_code
        raise SystemExit(code)
    monkeypatch.setattr(sys, "exit", fake_exit)
    try:
        healthcheck.main()
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 1

def test_healthcheck_missing_timestamp(monkeypatch, tmp_path):
    state, fake_open = run_healthcheck_with_state({}, tmp_path)
    monkeypatch.setattr("builtins.open", fake_open)
    exit_code = None
    def fake_exit(code):
        nonlocal exit_code
        raise SystemExit(code)
    monkeypatch.setattr(sys, "exit", fake_exit)
    try:
        healthcheck.main()
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 1

def test_healthcheck_corrupt_json(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("not a json")
    orig_open = open
    def fake_open(f, mode='r', *a, **k):
        if f == "state/state.json":
            return orig_open(state_file, mode)
        return orig_open(f, mode, *a, **k)
    monkeypatch.setattr("builtins.open", fake_open)
    exit_code = None
    def fake_exit(code):
        nonlocal exit_code
        raise SystemExit(code)
    monkeypatch.setattr(sys, "exit", fake_exit)
    try:
        healthcheck.main()
    except SystemExit as e:
        exit_code = e.code
    assert exit_code == 1 