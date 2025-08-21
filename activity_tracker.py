import os
from typing import Optional, Dict, Any, Union
from github import Github, GithubException, Auth
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from collections import Counter

class ActivityTracker:
    """
    A class to track development activity across GitHub repositories.
    Handles GitHub API authentication and provides methods for activity tracking.
    """

    def __init__(self, username: str, token: Optional[str] = None):
        """
        Initialize the ActivityTracker with GitHub API connection.

        Args:
            username: GitHub username.
            token: GitHub personal access token. If None, will try to get from GITHUB_TOKEN env var
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.username = username
        self.github: Optional[Github] = None
        self.user: Optional[Union[AuthenticatedUser, NamedUser]] = None
        self.stats: Dict[str, Dict[str, Any]] = {}
        self.rate_limit: Optional[Dict[str, Any]] = None

        self._setup_connection()

    def _setup_connection(self) -> None:
        """
        Set up the GitHub API connection and verify authentication.
        """
        try:
            if self.token:
                self.github = Github(
                    auth=Auth.Token(self.token),
                    per_page=100
                )
            else:
                self.github = Github(
                    per_page=100
                )

            # Test the connection by getting the authenticated user
            self.user = self.github.get_user(self.username)

            if self.user:
                print(f"Successfully connected to GitHub as: {self.user.login}")

        except GithubException as e:
            if e.status == 401:
                raise ValueError("Invalid GitHub token. Please check your authentication credentials.")
            elif e.status == 403:
                raise ValueError("GitHub API rate limit exceeded or insufficient permissions.")
            else:
                raise ConnectionError(f"Failed to connect to GitHub API: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error connecting to GitHub: {e}")

    def get_user_event_activity(self) -> Dict[str, Any]:
        """
        Get activity data for the user.
        """
        if not self.github or not self.user:
            raise RuntimeError("GitHub connection not established.")

        if isinstance(self.user, AuthenticatedUser):
            events = self.user.get_events()
        else:
            events = self.user.get_public_events()

        for event in events:
            repo_name = event.repo.name
            repo_stats = self.stats.setdefault(repo_name, dict(name = repo_name, counter = Counter(), owned = False))

            event_type = event.type
            if event_type == "PushEvent":
                repo_stats['counter']['pushes'] += 1
            elif event_type == "PullRequestEvent":
                repo_stats['counter']['pull_requests'] += 1
            elif event_type == "IssueCommentEvent":
                repo_stats['counter']['issue_comments'] += 1
            elif event_type == "IssueEvent":
                repo_stats['counter']['issues'] += 1
            elif event_type == "PullRequestReviewCommentEvent":
                repo_stats['counter']['pull_request_comments'] += 1
            elif event_type == "PullRequestReviewEvent":
                repo_stats['counter']['pull_request_reviews'] += 1
            else:
                repo_stats['counter'][event_type] += 1

            if event.repo.name.lower().split("/")[0] == self.username.lower():
                repo_stats['owned'] = True

        return {
            'stats': [repo_stats for repo_stats in self.stats.values()],
        }


    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current GitHub API rate limit information.

        Returns:
            Dictionary containing rate limit details.
        """
        if not self.github:
            raise RuntimeError("GitHub connection not established.")

        if self.rate_limit is None:
            try:
                rate_limit = self.github.get_rate_limit()
                self.rate_limit = {
                    'limit': rate_limit.core.limit,
                    'remaining': rate_limit.core.remaining,
                    'reset_time': rate_limit.core.reset.isoformat() if rate_limit.core.reset else None,
                    'search_limit': rate_limit.search.limit,
                    'search_remaining': rate_limit.search.remaining
                }
            except GithubException as e:
                raise RuntimeError(f"Failed to fetch rate limit info: {e}")

        return self.rate_limit

    def close(self) -> None:
        """
        Close the GitHub API connection.
        """
        if self.github:
            self.github.close()
            self.github = None
            self.user = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
