"""
Tests for src/component/checkers/version_checker.py
and src/repo_manager.py
"""

import pytest
import subprocess
from packaging.version import Version
from unittest.mock import patch

from src.build_classes import InstallEntry
from src.component.checkers.version_checker import VersionChecker
from src.repo_manager import RepoManager
from src.build_classes import RepoUpstream
from src.exceptions import GitError


def make_entry() -> InstallEntry:
    return InstallEntry(type="hardlink", source="/src/config", target="/target/config")


class TestVersionChecker:
    def test_returns_upgrade_when_new_greater(self):
        checker = VersionChecker(make_entry(), Version("2.0.0"), Version("1.0.0"))
        assert checker.check_version() == "upgrade"

    def test_returns_downgrade_when_new_lesser(self):
        checker = VersionChecker(make_entry(), Version("1.0.0"), Version("2.0.0"))
        assert checker.check_version() == "downgrade"

    def test_returns_reinstall_when_equal(self):
        checker = VersionChecker(make_entry(), Version("1.0.0"), Version("1.0.0"))
        assert checker.check_version() == "reinstall"


class TestRepoManager:
    def test_resolves_github_url(self):
        upstream = RepoUpstream(
            repo="user/repo", branch="main", commit=None, provider="github"
        )
        rm = RepoManager(upstream)
        assert rm.url == "https://github.com/user/repo"

    def test_resolves_gitlab_url(self):
        upstream = RepoUpstream(
            repo="user/repo", branch="main", commit=None, provider="gitlab"
        )
        rm = RepoManager(upstream)
        assert rm.url == "https://gitlab.com/user/repo"

    def test_resolves_raw_url(self):
        upstream = RepoUpstream(
            repo="https://example.com/repo.git",
            branch=None,
            commit=None,
            provider="url",
        )
        rm = RepoManager(upstream)
        assert rm.url == "https://example.com/repo.git"

    def test_returns_none_url_when_no_provider(self):
        upstream = RepoUpstream(
            repo="user/repo", branch="main", commit=None, provider=None
        )
        rm = RepoManager(upstream)
        assert rm.url is None

    def test_raises_on_invalid_repo_format(self):
        upstream = RepoUpstream(
            repo="not-valid", branch="main", commit=None, provider="github"
        )
        with pytest.raises(ValueError):
            RepoManager(upstream)

    def test_git_clone_raises_git_error_on_failure(self):
        upstream = RepoUpstream(
            repo="user/repo", branch="main", commit=None, provider="github"
        )
        rm = RepoManager(upstream)
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            with pytest.raises(GitError):
                rm.git_clone("https://github.com/user/repo", "/tmp/dest", "main")

    def test_git_checkout_raises_git_error_on_failure(self):
        upstream = RepoUpstream(
            repo="user/repo", branch="main", commit=None, provider="github"
        )
        rm = RepoManager(upstream)
        with patch(
            "subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")
        ):
            with pytest.raises(GitError):
                rm.git_checkout("abc123", "/tmp/dest")
