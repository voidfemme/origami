from pathlib import Path


class GitError(Exception):
    pass


class UpstreamNotDefinedError(Exception):
    def __init__(self, upstream_url: str) -> None:
        pass


class VersionCheckerError(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class OptionalEnvNotFoundError(Exception):
    pass


class RequiredEnvNotFoundError(Exception):
    pass


class FontNotFoundError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class ConfigNotFoundError(Exception):
    pass


class ProgramNotFoundError(Exception):
    pass


class MissingConfigKeyError(Exception):
    pass


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


class RiceNotExistsError(Exception):
    def __init__(self, rice: str) -> None:
        self.rice = rice

    def __str__(self) -> str:
        return f"Rice {self.rice} doesn't exist"
