from pathlib import Path
import logging

from src.exceptions import UnsupportedOsError

logger = logging.getLogger(__file__)


class FontInstaller:
    def __init__(
        self,
        operating_system: str,
    ) -> None:
        self.operating_system = operating_system.lower()

    def install_font(self, font_path: Path | str) -> None:
        font_path = Path(font_path)
        source_path = font_path.expanduser()
        font_dir: Path
        # -- LINUX/TERMUX --
        # - copy or symlink the font file into ~/.local/share/fonts
        # - run `fc-cache -f` to rebuild the fontconfig cache.
        if self.operating_system == "linux":
            font_dir = Path.home() / ".local/share/fonts"

        # -- MACOS --
        # - copy or symlink the font file into ~/Library/Fonts
        elif self.operating_system == "darwin":
            font_dir = Path.home() / "Library/Fonts"
        else:
            logger.error(
                f"Unsupported OS for font installation: {self.operating_system}"
            )
            raise UnsupportedOsError

        # 2. Ensure the destination directory exists
        font_dir.mkdir(parents=True, exist_ok=True)

        # 3. Define the target path (Handle existing links/files)
        target_path: Path = font_dir / source_path.name

        # 4. Create the symlink (Handle existing links/files)
        try:
            if target_path.exists() or target_path.is_symlink():
                if target_path.is_symlink() and target_path.readlink():
                    logger.debug(f"Font {source_path.name} is already correctly linked")
                    return
                else:
                    # If a different font/file exists there, back it up and remove it
                    logger.info(
                        f"Existing font found at {target_path}, removing to relink."
                    )
                    target_path.unlink()
            target_path.symlink_to(source_path)
            logger.info(f"Installed font: {source_path.name}")

            # 5. Refresh font cache (Linux only)
            if self.operating_system == "linux":
                import subprocess

                subprocess.run(["fc-cache", "-f"], check=False)
        except Exception as e:
            logger.error(f"Error installing font: {e}")
            print(f"Error installing font: {e}")  # TODO: remove this print statement
