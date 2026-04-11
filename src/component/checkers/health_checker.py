from pathlib import Path
from src.build_classes import BuildFile
from src.rice import Rice
from src.health_classes import ComponentHealth, RiceHealth
from src.component import Component

import platform
import shutil


class HealthChecker:
    def __init__(self, operating_system: str | None = None) -> None:
        self.operating_system = operating_system or platform.system().lower()

    def check_rice(self, rice: Rice) -> RiceHealth:
        health = RiceHealth(name=rice.theme_name)
        for component in rice.components:
            health.components.append(self.check_component(component))
        return health

    def check_component(self, component: Component) -> ComponentHealth:
        build = component.build_config
        health = ComponentHealth(name=build.name)

        self._check_symlinks(build, health)
        self._check_programs(build, health)
        self._check_fonts(build, health)
        self._check_config_paths(build, health)
        self._check_env_vars(build, health)

        return health

    def _check_symlinks(self, build: BuildFile, health: ComponentHealth) -> None:
        install_list = build.install
        os_installs = getattr(install_list, self.operating_system, None)
        if not os_installs:
            health.failing.append(f"No install entries for OS: {self.operating_system}")
            return
        for op in os_installs:
            target = Path(op.target).expanduser()
            if not target.exists() and not target.is_symlink():
                health.failing.append(f"Missing symlink target: {target}")
            elif target.is_symlink():
                source = Path(op.source).expanduser()
                if target.resolve() != source.resolve():
                    health.failing.append(
                        f"Symlink mismatch: {target} -> {target.resolve()}) "
                        f"(expected {source})"
                    )
                else:
                    health.passing.append(f"Symlink ok: {target}")
            else:
                health.failing.append(f"Target exists but is not a symlink: {target}")

    def _check_programs(self, build: BuildFile, health: ComponentHealth) -> None:
        if not build.deps or not build.deps.programs:
            return
        for program in build.deps.programs:
            if shutil.which(program.name):
                health.passing.append(f"Program found: {program.name}")
            else:
                msg = f"Program missing: {program.name}"
                if program.notes:
                    msg += f" ({program.notes})"
                if program.required:
                    health.failing.append(msg)
                else:
                    health.passing.append(f"Optional {msg}")

    def _check_fonts(self, build: BuildFile, health: ComponentHealth) -> None:
        if not build.deps or not build.deps.fonts:
            return
        if self.operating_system in ("linux", "termux"):
            font_dir = Path.home() / ".local/share/fonts"
        elif self.operating_system == "darwin":
            font_dir = Path.home() / "Library/Fonts"
        else:
            health.failing.append(
                f"Unsupported OS for font check: {self.operating_system}"
            )
            return
        for font in build.deps.fonts:
            matches = list(font_dir.glob(f"*{font.name}*"))
            if matches:
                health.passing.append(f"Font found: {font.name}")
            elif font.required:
                health.failing.append(f"Font missing: {font.name}")
            else:
                health.passing.append(f"Optional font missing: {font.name}")

    def _check_config_paths(self, build: BuildFile, health: ComponentHealth) -> None:
        if not build.deps or not build.deps.configs:
            return
        for config in build.deps.configs:
            if not config.path:
                continue
            p = Path(config.path).expanduser()
            if p.exists():
                health.passing.append(f"Config path exists: {p}")
            elif config.required:
                health.failing.append(f"Config path missing: {p}")
            else:
                health.passing.append(f"Optional config path missing: {p}")

    def _check_env_vars(self, build: BuildFile, health: ComponentHealth):
        if not build.deps or not build.deps.env:
            return
        import os

        for var in build.deps.env:
            if os.environ.get(var.name):
                health.passing.append(f"Env var set: {var.name}")
            elif var.required:
                health.failing.append(f"Env var missing: {var.name}")
            else:
                health.passing.append(f"Optional env var missing: {var.name}")


def print_health_report(health: RiceHealth) -> None:
    status = "HEALTHY" if health.is_healthy else "UNHEALTHY"
    print(f"\n=== Health Report: {health.name} [{status}] ===")
    for component in health.components:
        c_status = "OK" if component.is_healthy else "FAIL"
        print(f"\n  Component: {component.name} [{c_status}]")
        for item in component.passing:
            print(f"    [+] {item}")
        for item in component.failing:
            print(f"    [!] {item}")
    print()
