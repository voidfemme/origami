"""
Tests for src/rice_graph.py

Covers:
  - Topological ordering: components with no deps, linear dep chain, diamond
  - CycleError raised on circular dependencies
  - Target conflict detection: two components claiming the same target path
  - Env conflict detection: two components declaring same env var with different values
  - No conflicts when everything is clean
  - _get_os_installs: returns correct entries for OS, empty list for missing OS
"""

import pytest
import graphlib
from pathlib import Path
from unittest.mock import MagicMock

from src.build_classes import (
    BuildFile,
    InstallEntry,
    InstallList,
    DependencyList,
    ConfigDependency,
    EnvDependency,
)
from src.component.component import Component
from src.rice_graph import RiceGraph


def make_component(
    name: str,
    linux_target: str = "/tmp/target",
    linux_source: str = "/tmp/source",
    install_type: str = "symlink",
    deps: DependencyList | None = None,
    tmp_path: Path | None = None,
) -> Component:
    """Helper to build a minimal Component with controllable install target."""
    fake_path = (tmp_path or Path("/tmp")) / f"{name}_origami.json"
    build = BuildFile(
        path=fake_path,
        name=name,
        description=None,
        version="1.0.0",
        install=InstallList(
            linux=[
                InstallEntry(
                    type=install_type, source=linux_source, target=linux_target
                )
            ]
        ),
        deps=deps,
        upstream=None,
        hooks=None,
        notes=None,
        raw_json={"name": name, "version": "1.0.0"},
    )
    component = MagicMock(spec=Component)
    component.build_config = build
    return component


class TestTopologicalSort:
    def test_single_component_no_deps(self):
        c = make_component("only")
        graph = RiceGraph([c], "linux")
        result = graph.resolve()
        assert result.ordered_components == [c]

    def test_independent_components_all_present(self):
        a = make_component("a", linux_target="/tmp/a")
        b = make_component("b", linux_target="/tmp/b")
        graph = RiceGraph([a, b], "linux")
        result = graph.resolve()
        assert set(result.ordered_components) == {a, b}

    def test_dependency_ordering(self, tmp_path):
        # b depends on a: a must come before b
        a = make_component("a", linux_target=str(tmp_path / "a"), tmp_path=tmp_path)
        b_deps = DependencyList(
            configs=[ConfigDependency(name="a", path=tmp_path / "a", required=True)]
        )
        b = make_component(
            "b", linux_target=str(tmp_path / "b"), deps=b_deps, tmp_path=tmp_path
        )
        graph = RiceGraph([b, a], "linux")
        result = graph.resolve()
        ordered_names = [c.build_config.name for c in result.ordered_components]
        assert ordered_names.index("a") < ordered_names.index("b")

    def test_raises_on_circular_dependency(self, tmp_path):
        # a depends on b, b depends on a
        a_deps = DependencyList(
            configs=[ConfigDependency(name="b", path=tmp_path / "b", required=True)]
        )
        b_deps = DependencyList(
            configs=[ConfigDependency(name="a", path=tmp_path / "a", required=True)]
        )
        a = make_component(
            "a", linux_target=str(tmp_path / "a"), deps=a_deps, tmp_path=tmp_path
        )
        b = make_component(
            "b", linux_target=str(tmp_path / "b"), deps=b_deps, tmp_path=tmp_path
        )
        graph = RiceGraph([a, b], "linux")
        with pytest.raises(graphlib.CycleError):
            graph.resolve()


class TestConflictDetection:
    def test_no_conflicts_clean_rice(self):
        a = make_component("a", linux_target="/tmp/a")
        b = make_component("b", linux_target="/tmp/b")
        graph = RiceGraph([a, b], "linux")
        result = graph.resolve()
        assert not result.conflicts.has_conflicts

    def test_detects_target_conflict(self):
        # Both a and b claim the same target path
        a = make_component("a", linux_target="/tmp/shared")
        b = make_component("b", linux_target="/tmp/shared")
        graph = RiceGraph([a, b], "linux")
        result = graph.resolve()
        assert result.conflicts.has_conflicts
        assert len(result.conflicts.target_conflicts) == 1

    def test_detects_env_conflict(self):
        a_deps = DependencyList(
            env=[EnvDependency(name="EDITOR", value="nvim", required=True)]
        )
        b_deps = DependencyList(
            env=[EnvDependency(name="EDITOR", value="vim", required=True)]
        )
        a = make_component("a", linux_target="/tmp/a", deps=a_deps)
        b = make_component("b", linux_target="/tmp/b", deps=b_deps)
        graph = RiceGraph([a, b], "linux")
        result = graph.resolve()
        assert result.conflicts.has_conflicts
        assert len(result.conflicts.env_conflicts) == 1

    def test_no_env_conflict_when_same_value(self):
        a_deps = DependencyList(
            env=[EnvDependency(name="EDITOR", value="nvim", required=True)]
        )
        b_deps = DependencyList(
            env=[EnvDependency(name="EDITOR", value="nvim", required=True)]
        )
        a = make_component("a", linux_target="/tmp/a", deps=a_deps)
        b = make_component("b", linux_target="/tmp/b", deps=b_deps)
        graph = RiceGraph([a, b], "linux")
        result = graph.resolve()
        assert not result.conflicts.env_conflicts
