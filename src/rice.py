from pathlib import Path
from src.build_loader import BuildLoader
from src.component.component import Component
from src.rice_graph import RiceGraph
import logging
import os
import platform
import subprocess

logger = logging.getLogger(__name__)


class Rice:
    def __init__(
        self, theme_name: str, theme_path: Path, origami_config: Path | None = None
    ) -> None:
        self.theme_name = theme_name
        self.theme_path = theme_path
        self.active_os = platform.system()
        if origami_config:
            self.origami_config = origami_config
        else:
            self.origami_config = Path(os.path.expanduser("~/.config/origami"))
        self.components: list[Component] = self.collect_components()
        self.active: bool = False

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.theme_name == other
        return NotImplemented

    def activate(self) -> None:
        self.active = True

    def deactivate(self) -> None:
        self.active = False

    def apply_rice(self) -> None:
        rice_graph = RiceGraph(self.components, self.active_os).resolve()
        if rice_graph.conflicts.has_conflicts:
            target_conflict_msg = ""
            env_conflict_msg = ""
            for conflict in rice_graph.conflicts.target_conflicts:
                component_a = conflict.component_a
                component_b = conflict.component_b
                target_path = conflict.target_path
                target_conflict_msg += (
                    f"  - '{component_a}' conflicts with {component_b}\n"
                    f"    path: {target_path}\n"
                )

            for conflict in rice_graph.conflicts.env_conflicts:
                component_a = conflict.component_a
                component_b = conflict.component_b
                var_name = conflict.var_name
                value_a = conflict.value_a
                value_b = conflict.value_b
                env_conflict_msg += (
                    f"  - '{var_name}' is defined by\n"
                    f"    '{component_a}' as '{value_a}' and\n"
                    f"    '{component_b}' as '{value_b}'\n"
                )
            if target_conflict_msg:
                target_conflict_msg = f"Target conflicts:\n{target_conflict_msg}"
            if env_conflict_msg:
                env_conflict_msg = (
                    f"Environment variable conflicts:\n{env_conflict_msg}"
                )
            logger.error(
                f"The dependency graph has conflicts:\n{target_conflict_msg}{env_conflict_msg}",
            )  # NOTE: full resolution UI is future work

        for component in rice_graph.ordered_components:
            component.apply_all_components()

    def delete_rice(self) -> None:
        self.deactivate()
        if self.theme_path.exists():
            os.rmdir(self.theme_path)

    def collect_components(self) -> list[Component]:
        components = []
        for dir in os.listdir(self.theme_path):
            build_path = self.theme_path / dir / "origami.json"
            if not build_path.exists():
                continue
            # Create Build File for each component
            component = Component(
                operating_system=self.active_os,
                theme=self.theme_name,
                build_config=BuildLoader.from_path(build_path),
                origami_config=self.origami_config,
            )
            components.append(component)
        return components
