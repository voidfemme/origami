from pathlib import Path

class NoInstallationError(Exception):
    def __init__(self, build_path: str | Path):
        self.build_file_path = build_path

    def __str__(self) -> str:
        return f"Cannot install: No installations defined in {self.build_file_path}."

class BadInstallationTypeError(Exception):
    def __init__(self, filetype: str) -> None:
        self.filetype = filetype

    def __str__(self) -> str:
        return f"File type: {self.filetype} is not supported for installation."

class UnsupportedOsError(Exception):
    def __str__(self) -> str:
        return "Unsupported OS for installation."

class MissingTermuxPrefixError(Exception):
    def __str__(self) -> str:
        return "Missing Termux prefix"
