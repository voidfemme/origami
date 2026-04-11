import graphlib
import logging
from pathlib import Path
from dataclasses import dataclass

from src.build_classes import BuildFile, SymlinkOp
from src.component import Component
from src.conflict_classes import EnvConflict, RiceConflicts, TargetConflict

logger = logging.getLogger(__name__)


@dataclass
class GraphResult:
    ordered_components: list[Component]
    conflicts: RiceConflicts


class RiceGraph:
    def __init__(self, components: list[Component], operating_system: str) -> None:
        self.components = components
        if operating_system == "macos":
            self.operating_system = "darwin"
        else:
            self.operating_system = operating_system
        self._component_map: dict[str, Component] = {
            c.build_config.name: c for c in components
        }

    def resolve(self) -> GraphResult:
        edges = self._build_edges()
        ordered = self._topological_sort(edges)
        conflicts = self._detect_conflicts()
        return GraphResult(ordered_components=ordered, conflicts=conflicts)

    def _get_os_installs(self, build: BuildFile) -> list[SymlinkOp]:
        return getattr(build.install, self.operating_system, None) or []

    def _build_edges(self) -> dict[str, set[str]]:
        """
        Returns a dict of { component_name: {set of component_names it depends on} }
        for use with TopologicalSorter.
        """
        edges: dict[str, set[str]] = {
            c.build_config.name: set() for c in self.components
        }

        for component in self.components:
            build = component.build_config
            if not build.deps or not build.deps.configs:
                continue

            for config_dep in build.deps.configs:
                dep_name = config_dep.name
                dep_component = self._component_map.get(dep_name)

                if dep_component is None:
                    if config_dep.required:
                        raise ValueError(
                            f"Component '{build.name}' requires '{dep_name}', "
                            "but no component with that name exists in this rice."
                        )
                    else:
                        logger.warning(
                            f"Component '{build.name}' has optional dependency '{dep_name}', "
                            "which was not found. Skipping."
                        )
                        continue

                # Validate that the matched component's OS-specific install target
                # matches the declared path on the config dependency
                if config_dep.path:
                    declared_path = Path(config_dep.path).expanduser().resolve()
                    os_installs = self._get_os_installs(dep_component.build_config)
                    actual_targets = [
                        Path(op.target).expanduser().resolve() for op in os_installs
                    ]
                    if declared_path not in actual_targets:
                        operating_system = (
                            self.operating_system
                            if not self.operating_system == "darwin"
                            else "macos"
                        )
                        if config_dep.required:
                            raise ValueError(
                                f"Component '{build.name}' depends on '{dep_name}' at path "
                                f"'{config_dep.path}', but no {operating_system} install "
                                f"target for '{dep_name}' matches that path."
                            )
                        else:
                            logger.warning(
                                f"Component '{build.name}' optional dependency '{dep_name}' "
                                f"declared path '{config_dep.path}', does not match any "
                                f"{operating_system} install target. Skipping."
                            )
                edges[build.name].add(dep_name)
        return edges

    def _topological_sort(self, edges: dict[str, set[str]]) -> list[Component]:
        try:
            sorter = graphlib.TopologicalSorter(edges)
            ordered_names = list(sorter.static_order())
        except graphlib.CycleError as e:
            raise graphlib.CycleError(
                f"Circular dependency detected among components: {e.args[1]}"
            ) from e
        return [self._component_map[name] for name in ordered_names]

    def _detect_conflicts(self) -> RiceConflicts:
        target_conflicts: list[TargetConflict] = []
        env_conflicts: list[EnvConflict] = []

        self._find_target_conflicts(target_conflicts)
        self._find_env_conflicts(env_conflicts)

        return RiceConflicts(
            target_conflicts=target_conflicts,
            env_conflicts=env_conflicts,
        )

    def _find_target_conflicts(self, target_conflicts: list[TargetConflict]) -> None:
        # Map each resolved target path -> the component that claims it
        seen: dict[Path, Component] = {}

        for component in self.components:
            for op in self._get_os_installs(component.build_config):
                target = Path(op.target).expanduser().resolve()
                if target in seen:
                    target_conflicts.append(
                        TargetConflict(
                            component_a=seen[target].build_config.name,
                            component_b=component.build_config.name,
                            target_path=target,
                        )
                    )
                else:
                    seen[target] = component

    def _find_env_conflicts(self, env_conflicts: list[EnvConflict]) -> None:
        # Map each env var name -> (value, component name) of first declaration
        seen: dict[str, tuple[str, str]] = {}

        for component in self.components:
            build = component.build_config
            if not build.deps or not build.deps.env:
                continue
            for env in build.deps.env:
                var_name = env.name
                if var_name in seen:
                    existing_value, existing_component = seen[var_name]
                    if existing_value != env.value:
                        env_conflicts.append(
                            EnvConflict(
                                component_a=existing_component,
                                component_b=build.name,
                                var_name=var_name,
                                value_a=existing_value,
                                value_b=env.value,
                            )
                        )
                    else:
                        seen[var_name] = (env.value, build.name)
