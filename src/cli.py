import typer
from pathlib import Path

from src.origami_config import OrigamiConfig

"""
= CLI CLASS =
Commands to implement:
- origami apply <theme>
- origami remove <theme>
- origami list
- origami status <theme>
- origami update <theme>
- origami theme set <theme>
- origami theme list
"""

# OUTPUT:
# typer.echo("Hello, world!")
# typer.secho("Hello, world!", fg=typer.colors.RED, err=True)

app = typer.Typer()
theme_app = typer.Typer()
app.add_typer(theme_app, name="theme")

default_config_path = Path("~/.config/origami").expanduser()


@app.command()
def apply(
    theme: str,
    dry_run: bool = False,
    target_os: str | None = typer.Option(None),
    config_dir: str | None = typer.Option(None),
):
    """Apply a rice theme."""
    if config_dir:
        origami_config_dir = Path(config_dir)
    else:
        origami_config_dir = default_config_path
    target_os = target_os if target_os else None
    ricer = OrigamiConfig(origami_config_dir, target_os)
    ricer.apply_rice(theme)


@app.command()
def remove(theme: str):
    """Remove a rice theme (that's not currently active, otherwise error)"""
    pass


@app.command("list")
def app_list(config_dir: str | None = typer.Option(None)):
    if config_dir:
        origami_config_dir = Path(config_dir)
    else:
        origami_config_dir = default_config_path
    ricer = OrigamiConfig(origami_config_dir)
    ricer._get_available_rices()


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
