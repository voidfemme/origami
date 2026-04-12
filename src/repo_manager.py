from src.build_classes import RepoUpstream
from src.exceptions import GitError
import subprocess


class RepoManager:
    def __init__(self, upstream: RepoUpstream) -> None:
        self.provider = upstream.provider
        self.repo = self._validate_repo(upstream.repo)
        self.branch = upstream.branch
        self.commit = upstream.commit
        self.url = self._resolve_upstream(
            provider=self.provider,
            repo=self.repo,
        )

    def _validate_repo(self, repo: str | None) -> str | None:
        if repo is None:
            return None
        parts = repo.split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(
                f"Invalid repo format '{repo}': expected 'author/reponame'"
            )
        return repo

    def _resolve_upstream(
        self,
        provider: str | None = None,
        repo: str | None = None,
    ) -> str | None:
        if provider == "github" or provider == "gitlab":
            return f"https://{provider}.com/{repo}"
        elif provider == "url":
            return repo
        return None

    def git_clone(self, url: str, destination_dir: str, branch: str | None) -> None:
        cmd = (
            ["git", "clone", url, "--branch", branch, destination_dir]
            if branch
            else ["git", "clone", url, destination_dir]
        )
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise GitError(
                f"Failed to clone {url}: git exited with code {e.returncode}"
            )

    def git_checkout(self, commit: str, destination_dir: str) -> None:
        try:
            subprocess.run(["git", "checkout", commit], cwd=destination_dir, check=True)
        except subprocess.CalledProcessError as e:
            raise GitError(
                f"Failed to checkout {commit}: git exited with code {e.returncode}"
            )
