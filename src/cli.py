import typer
from pathlib import Path

from src.origami_config import OrigamiConfig

"""
= CLI CLASS =
Commands to implement:
- origami apply <theme>
- origami remove [option] <theme>
- origami list
- origami status <theme>
- origami update <theme>
- origami theme set <theme>
- origami theme list
- origami script add <script path>
"""

app = typer.Typer()
theme_app = typer.Typer()
remove_app = typer.Typer()
script_app = typer.Typer()
app.add_typer(theme_app, name="theme")
app.add_typer(remove_app, name="remove")
app.add_typer(script_app, name="script")

default_config_path = Path("~/.config/origami").expanduser()


def _get_ricer(config_dir: str | None = None) -> OrigamiConfig:
    """Lazily construct OrigamiConfig so import doesn't blow up."""
    path = Path(config_dir) if config_dir else default_config_path
    return OrigamiConfig(path)


@app.command()
def apply(
    theme: str,
    config_dir: str | None = typer.Option(None),
):
    """Apply a rice theme."""
    _get_ricer(config_dir).apply_rice(theme)


@app.command()
def remove(
    theme: str,
    config_dir: str | None = typer.Option(None),
):
    """Remove a rice theme (that's not currently active, otherwise error)"""
    typer.secho(
        f"Are you sure you want to remove {theme}?", fg=typer.colors.RED, err=False
    )
    typer.echo(
        f"This will delete its directory from '{default_config_path}/themes/{theme}' permanently"
    )
    _get_ricer(config_dir).delete_rice(theme)


@remove_app.command("-f")
def force(
    theme: str,
    config_dir: str | None = typer.Option(None),
):
    _get_ricer(config_dir).delete_rice(theme)


@app.command("list")
def app_list(config_dir: str | None = typer.Option(None)):
    _get_ricer(config_dir).get_available_rices()


@app.command()
def status(theme: str):
    pass


@app.command()
def update(theme: str):
    pass


@theme_app.command("set")
def theme_set(theme: str):
    pass


@theme_app.command("list")
def theme_list():
    pass


@script_app.command("add")
def add_script():
    pass
