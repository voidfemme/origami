from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TargetConflict:
    component_a: str
    component_b: str
    target_path: Path


@dataclass
class EnvConflict:
    component_a: str
    component_b: str
    var_name: str
    value_a: str
    value_b: str


@dataclass
class RiceConflicts:
    target_conflicts: list[TargetConflict] = field(default_factory=list)
    env_conflicts: list[EnvConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.target_conflicts or self.env_conflicts)


@dataclass
class ConflictResolution:
    pass
