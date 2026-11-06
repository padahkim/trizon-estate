"""Exercise the TDD hook using real Codex payloads and temporary files."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).with_name("tdd_guard.py")


def run_guard(project, tool_input, *, tool_name="apply_patch", cwd=None):
    workdir = cwd or project
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool_name,
               "cwd": str(workdir), "tool_input": tool_input}
    return subprocess.run(
        [sys.executable, str(GUARD)], input=json.dumps(payload),
        cwd=workdir, capture_output=True, text=True,
    )


def patch_for(path, action="Update"):
    return {"command": f"*** Begin Patch\n*** {action} File: {path}\n@@\n-old\n+new\n*** End Patch"}


@pytest.mark.parametrize("source", ["service.py", "service.ts", "widget.tsx", "service.js", "widget.jsx"])
def test_implementation_without_a_test_is_denied(tmp_path, source):
    result = run_guard(tmp_path, patch_for(source))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert source in output["permissionDecisionReason"]


@pytest.mark.parametrize("source,test", [
    ("scripts/service.py", "scripts/test_service.py"),
    ("src/service.py", "tests/test_service.py"),
    ("src/lib/service.py", "tests/lib/test_service.py"),
    ("src/lib/service.py", "tests/src/lib/test_service.py"),
    ("src/lib/service.ts", "src/lib/service.test.ts"),
    ("src/lib/service.ts", "src/lib/service.spec.ts"),
    ("src/lib/service.ts", "src/lib/__tests__/service.test.ts"),
    ("src/lib/service.ts", "src/__tests__/service.test.ts"),
    ("src/widget.tsx", "src/widget.test.jsx"),
])
def test_existing_corresponding_test_allows_implementation(tmp_path, source, test):
    test_path = tmp_path / test
    test_path.parent.mkdir(parents=True, exist_ok=True)
    test_path.write_text("# test written first\n")
    result = run_guard(tmp_path, patch_for(source))
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("path", [
    "scripts/test_service.py", "src/service.test.ts", "src/service.spec.tsx",
    "tests/unit/service.py", "src/__tests__/service.ts",
    "docs/TDD.md", "pyproject.toml", "package.json", "styles.css",
    "next.config.ts", "src/types/order.ts", "src/types.ts", "src/global.d.ts",
    "src/app/page.tsx", "src/app/layout.tsx", "scripts/__init__.py",
])
def test_tests_and_declarative_files_can_be_written_first(tmp_path, path):
    result = run_guard(tmp_path, patch_for(path, "Add"))
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("source", ["contest.py", "latest.ts", "src/speculation.ts", "test_project/src/service.py"])
def test_test_substrings_do_not_exempt_implementation(tmp_path, source):
    result = run_guard(tmp_path, patch_for(source))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("action", ["Add", "Update", "Delete"])
def test_every_file_in_a_patch_is_checked(tmp_path, action):
    command = f"*** Begin Patch\n*** Update File: README.md\n@@\n-a\n+b\n*** {action} File: service.py\n*** End Patch"
    result = run_guard(tmp_path, {"command": command})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_rename_checks_the_destination(tmp_path):
    result = run_guard(tmp_path, {"command": "*** Begin Patch\n*** Update File: test_service.py\n*** Move to: service.py\n@@\n-a\n+b\n*** End Patch"})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_test_added_in_the_same_patch_is_not_yet_written_first(tmp_path):
    result = run_guard(tmp_path, {"command": "*** Begin Patch\n*** Add File: test_service.py\n+pass\n*** Add File: service.py\n+pass\n*** End Patch"})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("tool_name", ["Edit", "Write"])
def test_direct_file_path_is_checked(tmp_path, tool_name):
    source = tmp_path / 'service "quoted".py'
    result = run_guard(tmp_path, {"file_path": str(source)}, tool_name=tool_name)
    assert result.returncode == 0, result.stderr
    assert source.name in json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"]


def test_subdirectory_session_resolves_tests_from_the_git_root(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_service.py").write_text("pass\n")
    result = run_guard(tmp_path, patch_for("service.py"), cwd=tmp_path / "src")
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_absolute_source_path_in_project_with_spaces(tmp_path):
    project = tmp_path / "project with spaces"
    project.mkdir()
    (project / "test_service.py").write_text("pass\n")
    result = run_guard(project, patch_for(project / "service.py"))
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("source,test", [("service.py", "test_service.py"), ("service.ts", "service.test.ts")])
def test_tests_outside_the_project_do_not_authorize_implementation(tmp_path, source, test):
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "init", "-q", str(project)], check=True, capture_output=True)
    outside_tests = tmp_path / "__tests__"
    outside_tests.mkdir()
    (outside_tests / test).write_text("pass\n")
    result = run_guard(project, patch_for(source))
    assert result.returncode == 0, result.stderr
    assert result.stdout, "A test outside the project incorrectly allowed implementation"
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("tool_input", [{}, {"command": ""}, {"command": ["*** Begin Patch", "*** Add File: README.md", "+doc", "*** End Patch"]}])
def test_non_source_input_does_not_block(tmp_path, tool_input):
    result = run_guard(tmp_path, tool_input)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
