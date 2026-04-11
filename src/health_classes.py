from dataclasses import dataclass, field


@dataclass
class ComponentHealth:
    name: str
    passing: list[str] = field(default_factory=list)
    failing: list[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return len(self.failing) == 0


@dataclass
class RiceHealth:
    name: str
    components: list[ComponentHealth] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return all(c.is_healthy for c in self.components)
