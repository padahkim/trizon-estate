"""Verify the native Codex hook configuration and guard protocol."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from codex_cli import codex_command

ROOT = Path(__file__).resolve().parent.parent
HOOKS_FILE = ROOT / ".codex" / "hooks.json"


def test_launcher_selects_project_without_registering_duplicate_hooks(tmp_path):
    project = tmp_path / "project with spaces"
    command = codex_command(project)
    assert command[command.index("--cd") + 1] == str(project)
    assert "features.hooks=true" in command
    assert not any(arg.startswith("hooks.") for arg in command)
    assert not any(arg.startswith("--dangerously-") for arg in command)


@pytest.fixture
def hook_project(tmp_path):
    project = tmp_path / "project with spaces"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    (project / "subdir").mkdir()
    subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
    for script in ("guard.py", "tdd_guard.py"):
        shutil.copyfile(ROOT / "scripts" / script, scripts / script)
    return project


def run_configured_hook(project, tool, command):
    config = json.loads(HOOKS_FILE.read_text())
    groups = config["hooks"]["PreToolUse"]
    matching = [group for group in groups if re.search(group["matcher"], tool)]
    assert len(matching) == 1, f"Expected one hook for {tool}"
    hook = matching[0]["hooks"][0]
    assert hook["type"] == "command"
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool,
               "cwd": str(project / "subdir"), "tool_input": {"command": command}}
    return subprocess.run(
        hook["command"], shell=True, cwd=project / "subdir",
        input=json.dumps(payload), capture_output=True, text=True,
    )


def test_configured_bash_hook_resolves_project_from_a_subdirectory(hook_project):
    result = run_configured_hook(hook_project, "Bash", "git reset --hard")
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


@pytest.mark.parametrize("tool", ["apply_patch", "Edit", "Write"])
def test_configured_tdd_hook_denies_then_allows_after_test_is_written(hook_project, tool):
    command = "*** Begin Patch\n*** Add File: ../service.py\n+pass\n*** End Patch"
    result = run_configured_hook(hook_project, tool, command)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    (hook_project / "test_service.py").write_text("pass\n")
    result = run_configured_hook(hook_project, tool, command)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("tool_name, key", [("Bash", "command"), ("exec_command", "cmd")])
def test_codex_destructive_shell_call_is_blocked(tool_name, key):
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool_name,
               "tool_input": {key: "git reset --hard"}}
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("guard.py"))],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


def test_codex_read_only_shell_call_is_allowed():
    payload = {"tool_name": "Bash", "tool_input": {"command": "git status --short"}}
    result = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("guard.py"))],
        input=json.dumps(payload), capture_output=True, text=True,
    )
    assert result.returncode == 0
