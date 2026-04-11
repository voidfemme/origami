from pathlib import Path
from packaging.version import Version
from jsonschema import SchemaError, ValidationError, validate as validate_json

import json

from src.build_classes import (
    BuildFile,
    ConfigDependency,
    DependencyList,
    EnvDependency,
    FontDependency,
    ProgramDependency,
    RepoUpstream,
    InstallHooks,
    InstallList,
    SymlinkOp,
)


class BuildLoader:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.schema: dict = self._load_schema(
            Path(__file__).parent / ".." / "assets" / "build_schema.json"
        )
        try:
            self.raw_data = self._load_and_validate(file_path)
            self.build = self._parse_to_dataclass(self.raw_data)
        except Exception as e:
            print(e)

    @classmethod
    def from_path(cls, path: Path | str) -> BuildFile:
        path = Path(path)
        instance = cls(path)
        return instance.build

    def _load_schema(self, path: str | Path) -> dict:
        with open(path) as json_schema:
            return json.load(json_schema)

    def _load_and_validate(self, path: str | Path) -> dict:
        # 1. Load JSON
        with open(path) as json_data:
            try:
                build_json = json.load(json_data)
            except json.JSONDecodeError as e:
                print(f"Malformed JSON: {e}")
                raise
            except FileNotFoundError as e:
                print(f"File not found: {e}")
                raise
            except PermissionError as e:
                print(f"Permission Error: {e}")
                raise
            except IsADirectoryError as e:
                print(f"File is a directory: {e}")
                raise
            except Exception as e:
                print(f"Other error: {e}")
                raise

        # 2. validate(instance, schema)
        try:
            validate_json(instance=build_json, schema=self.schema)
        except ValidationError as e:
            print(f"Validation Error!\n{e}")
            raise
        except SchemaError as e:
            print(f"Schema Error: {e}")
            raise
        except Exception as e:
            print(f"Other Error!\n{e}")
            raise

        # 3. Return data if successful
        return build_json

    def _parse_to_dataclass(self, data) -> BuildFile:
        # Handle nested lists in deps safely
        deps_raw: dict = data.get("deps", {})
        deps_obj: DependencyList | None = (
            DependencyList(
                programs=[ProgramDependency(**p) for p in deps_raw.get("programs", [])],
                configs=[ConfigDependency(**c) for c in deps_raw.get("configs", [])],
                paths=[Path(path) for path in deps_raw.get("paths", [])],
                fonts=[FontDependency(**f) for f in deps_raw.get("fonts", [])],
                env=[EnvDependency(**e) for e in deps_raw.get("env", [])],
            )
            if "deps" in data
            else None
        )

        # Install objects:
        install_raw: dict = data.get("install", {})
        linux = [SymlinkOp(**l) for l in install_raw.get("linux", [])] or None
        macos = [SymlinkOp(**m) for m in install_raw.get("macos", [])] or None
        termux = [SymlinkOp(**t) for t in install_raw.get("termux", [])] or None
        install_obj: InstallList | None = InstallList(
            linux=linux,
            macos=macos,
            termux=termux,
        )

        # Handle upstream safely
        upstream_raw: dict = data.get("upstream", {})
        upstream_obj: RepoUpstream | None = (
            RepoUpstream(**upstream_raw) if upstream_raw else None
        )

        # Handle hooks safely
        hooks_raw: dict = data.get("hooks", {})
        hooks_obj: InstallHooks | None = (
            InstallHooks(**hooks_raw) if hooks_raw else None
        )

        return BuildFile(
            path=self.file_path,
            name=data["name"],
            description=data.get("description"),
            version=data["version"],
            install=install_obj,
            deps=deps_obj,
            upstream=upstream_obj,
            hooks=hooks_obj,
            notes=data["notes"] if "notes" in data else None,
            raw_json=self.raw_data,
        )

    def print_build_config(self) -> None:
        print(f"Config Name: {self.build.name}")
        print(f"Config Path: {self.build.path}")
        print(f"Description: {self.build.description}")
        print(f"Version: {self.build.version}")
        print("Install:")
        if self.build.install:
            installation = self.build.install
            if installation.linux:
                for install in installation.linux:
                    print(f"  Linux:")
                    print(f"    - type: {install.type}")
                    print(f"    - source: {install.source}")
                    print(f"    - target: {install.target}")
            if installation.macos:
                for install in installation.macos:
                    print(f"  Mac OS:")
                    print(f"    - type: {install.type}")
                    print(f"    - source: {install.source}")
                    print(f"    - target: {install.target}")
            if installation.termux:
                for install in installation.termux:
                    print(f"  Termux:")
                    print(f"    - type: {install.type}")
                    print(f"    - source: {install.source}")
                    print(f"    - target: {install.target}")
        print("Dependencies:")
        # Check if deps exists
        if self.build.deps:
            dependencies = self.build.deps
            if dependencies.programs:
                print("  Programs:")
                # Iterate through the programs list
                for program in dependencies.programs:
                    # Use the 'program' variable from the loop, not index [0]
                    status = "(Required)" if program.required else ""
                    print(f"    - {program.name} {program.version or ''} {status}")
                    if program.notes:
                        print(f"      Note: {program.notes}")
            if dependencies.configs:
                print("  Configs:")
                for config in dependencies.configs:
                    status = "(Required)" if config.required else ""
                    print(f"    - {config.name} {status}")
            if dependencies.env:
                print("  Environment variables:")
                for variable in dependencies.env:
                    status = "(Required)" if variable.required else ""
                    print(f"    - {variable.name} {status}")
            if dependencies.fonts:
                print("  Fonts:")
                for font in dependencies.fonts:
                    status = "(Required)" if font.required else ""
                    print(f"    - {font.name} {status}")
            if dependencies.paths:
                print("  Required paths:")
                for path in dependencies.paths:
                    print(f"    - {path}")
        else:
            print("  No dependencies defined.")
        if self.build.upstream:
            print("Upstream:")
            print(f"  Repo: {self.build.upstream.repo}")
            print(f"  Branch: {self.build.upstream.branch}")
        else:
            print("No upstream repository defined.")
        if self.build.hooks:
            hooks = self.build.hooks
            print("Hooks:")
            print(f"  Pre-Install: {hooks.pre_install}")
            print(f"  Post-Install: {hooks.post_install}")
            print(f"  Pre-uninstall: {hooks.pre_uninstall}")
            print(f"  Post-uninstall: {hooks.post_uninstall}")
        else:
            print("No hooks defined.")
        if self.build.notes:
            print(f"Notes: {self.build.notes}")
        else:
            print("No notes.")

    @property
    def supported_environments(self):
        return [
            os
            for os in ["linux", "macos", "termux"]
            if getattr(self.build.install, os) is not None
        ]

    def get_version(self) -> Version:
        return Version(self.build.version)
