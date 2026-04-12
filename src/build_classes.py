from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InstallEntry:
    type: str
    source: str
    target: str


@dataclass
class InstallList:
    linux: list[InstallEntry] | None = None  # fields: method, target
    macos: list[InstallEntry] | None = None  # fields: method, target
    termux: list[InstallEntry] | None = None  # fields: method, target, prefix


@dataclass
class FontDependency:
    name: str
    required: bool


@dataclass(frozen=True)
class ProgramDependency:
    name: str = field(compare=True)
    version: str | None
    required: bool = field(compare=True)
    notes: str | None = None


@dataclass
class ConfigDependency:
    name: str
    path: Path
    required: bool


@dataclass
class EnvDependency:
    name: str
    value: str
    required: bool


@dataclass
class DependencyList:
    programs: list[ProgramDependency] | None = None
    configs: list[ConfigDependency] | None = None
    paths: list[Path] | None = None
    fonts: list[FontDependency] | None = None
    env: list[EnvDependency] | None = None


@dataclass
class RepoUpstream:
    repo: str
    branch: str | None
    commit: str | None
    provider: str | None


@dataclass
class InstallHooks:
    pre_install: list[str] | None = None
    post_install: list[str] | None = None
    pre_uninstall: list[str] | None = None
    post_uninstall: list[str] | None = None


@dataclass
class BuildFile:
    path: Path  # required, but not in the build.json
    name: str  # required
    description: str | None
    version: str  # required
    install: InstallList  # required
    deps: DependencyList | None
    upstream: RepoUpstream | None
    hooks: InstallHooks | None
    notes: str | None
    raw_json: dict
