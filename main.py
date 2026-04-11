#!/bin/env python3
import shutil
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def install_new_theme(
    config_path: Path,
    default_config: Path = Path(__file__).parent / ".." / "assets" / "origami",
) -> None:
    origami_config: Path = config_path / "origami"
    theme_folder: Path = Path(
        input(
            "Enter the path to the folder.\nLeave blank and hit enter to download from online repo instead: "
        )
    )
    if str(theme_folder) is None:
        theme_repo = input("Enter repository url (Leave blank to cancel): ")
        if theme_repo is None:
            print("Cancelling. Good bye.")
            exit(0)
    theme_name = input("Enter a name for your theme: ")
    # TODO: Check build file for newly added theme, before just copying it into the
    # origami config directory under `~/.config/origami/`
    try:
        if os.path.exists(origami_config):
            # Copy the file at `f"./assets/origami/themes/{theme_folder}"` to
            # `f"~/.config/origami/themes/{theme_folder}"`
            shutil.copytree(theme_folder, origami_config / theme_name)
        else:
            # Origami config doesn't exist; install a fresh origami config
            shutil.copytree(default_config, origami_config)
    except Exception as e:
        print(f"Oopsies! -- {e}")
        exit(1)
    print("New theme installed successfully")


def switch_theme(origami_config: Path):
    new_theme = ""
    print("Available themes: ")
    themes = os.listdir(origami_config / "themes")
    for theme in themes:
        print(theme)
    while True:
        new_theme = input("Enter theme name: ")  # This will end up being the name of
        # the theme folder
        if new_theme not in themes:
            print("Invalid theme, please select from this list:")
            for theme in themes:
                print(theme)
        else:
            break

    # Validate the new theme build files


def main():
    # Get cmd-line args. are we
    #   - installing a new theme?
    #   - switching themes?
    #   - health check?
    # TODO: For now, just create the bools, and edit it later to get cmd args
    installing_new_theme: bool = True
    switching_theme: bool = True
    health_check: bool = True

    # Set up variables for later
    theme_prompt: str = ""

    # Define important paths
    config_path = Path("~/.config")
    default_config = Path(__file__).parent / ".." / "assets" / "origami"
    origami_config = config_path / "origami"

    # --- INSTALL A NEW THEME ---
    if installing_new_theme:
        install_new_theme(config_path, default_config)

    # --- SWITCH THEME ---
    theme_prompt: str = input("Do you want to a apply a new theme? (y,n)")
    if theme_prompt == "y" or switching_theme:
        switch_theme(origami_config)
    # Load all the build files
    # Build the dependency graph
    #   - If errors, automatically fix or display an error to the user (or include in health check)
    # Check that all necessary file paths exist on the system, and in the theme file
    # IF any file path doesn't exist
    #   - automatically restore missing file paths or display missing file error (or include in health check)
    # IF checking_health:
    #   - check version numbers
    #   - check script paths
    #   - other build data corresponds with build.json
    #   - Print a diagnostics message for the whole theme
    #   - Exit the program
    # IF swtching_theme:
    #   - symlink the correct directories/files in `~/.config/` or in `~/` depending on what's being installed
    # Print success message to user
