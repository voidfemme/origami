from pathlib import Path


class ScriptInstaller:
    def __init__(
        self, origami_config: Path | str, scripts_dir: Path | str | None = None
    ) -> None:
        self.origami_config = Path(origami_config)
        if scripts_dir:
            self.scripts_dir = scripts_dir
        else:
            self.scripts_dir = self.origami_config / "scripts"

    @classmethod
    def install_script(cls, script: Path | str) -> None:
        pass
