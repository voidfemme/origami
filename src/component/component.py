import logging
from pathlib import Path
from src.build_classes import BuildFile, FontDependency, SymlinkOp
from src.component.checkers import DependencyChecker
from src.component.installers import Installer, FontInstaller

logger = logging.getLogger(__name__)


class Component:
    def __init__(
        self,
        operating_system: str,
        theme: str,
        build_config: BuildFile,
        origami_config: Path | None,
    ) -> None:
        if operating_system == "macos":
            self.operating_system = "darwin"
        else:
            self.operating_system = operating_system.lower()

        if not origami_config:
            self.origami_config = Path.home() / ".config/origami"
        else:
            self.origami_config = origami_config

        self.theme = theme
        self.origami_theme_path = self.origami_config / self.theme
        self.origami_script_path = self.origami_config / "scripts"
        self.build_config = build_config
        self.build_config_path = self.build_config.path
        self.fonts_dir = self.origami_config / "themes" / self.theme / "fonts"
        self.installer = Installer(
            self.build_config,
            Path(self.origami_config),
            self.operating_system,
            self.theme,
        )
        if self.build_config.deps:
            self.dependency_checker = DependencyChecker(
                self.build_config.deps, self.operating_system
            )
            self.font_installer = FontInstaller(self.operating_system)
        self.installations: list[SymlinkOp] = self.installer.get_install_objects()

    def apply_all_components(self) -> None:
        for component in self.installations:
            self.installer.apply_component(component)

    def get_required_paths(self) -> list[Path] | None:
        if self.build_config.deps:
            paths = self.build_config.deps.paths
        else:
            logger.log(logging.DEBUG, "Build file requires no paths to exist.")
            paths = []
        return paths

    def get_missing_fonts(self) -> list[FontDependency]:
        return self.dependency_checker.verify_fonts()

    def apply_fonts(self) -> None:
        if self.build_config.deps:
            if self.build_config.deps.fonts:
                for font in self.get_missing_fonts():
                    if font:
                        font_path = self.fonts_dir / font.name
                        self.font_installer.install_font(font_path)

    def check_upstream(self) -> None:
        if self.build_config.upstream:
            pass

    def check_health(self):
        # Do the _symlinks_ exist at their expected target locations? Do they point to the right place?
        # Should I use a separate HealthChecker() object?
        pass
