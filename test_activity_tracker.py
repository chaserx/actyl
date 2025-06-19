import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from github import Github, GithubException, Auth
from github.AuthenticatedUser import AuthenticatedUser
from github.NamedUser import NamedUser
from collections import Counter

from activity_tracker import ActivityTracker


class TestActivityTracker:
    """Test cases for ActivityTracker class."""

    @pytest.fixture
    def mock_github(self):
        """Mock GitHub API client."""
        return Mock(spec=Github)

    @pytest.fixture
    def mock_authenticated_user(self):
        """Mock authenticated GitHub user."""
        user = Mock(spec=AuthenticatedUser)
        user.login = "testuser"
        return user

    @pytest.fixture
    def mock_named_user(self):
        """Mock named GitHub user."""
        user = Mock(spec=NamedUser)
        user.login = "testuser"
        return user

    @pytest.fixture
    def sample_events(self):
        """Sample GitHub events for testing."""
        events = []
        
        # Push event
        push_event = Mock()
        push_event.type = "PushEvent"
        push_event.repo.name = "testuser/repo1"
        events.append(push_event)
        
        # Pull request event
        pr_event = Mock()
        pr_event.type = "PullRequestEvent"
        pr_event.repo.name = "testuser/repo1"
        events.append(pr_event)
        
        # Issue comment event
        comment_event = Mock()
        comment_event.type = "IssueCommentEvent"
        comment_event.repo.name = "otheruser/repo2"
        events.append(comment_event)
        
        # Issue event
        issue_event = Mock()
        issue_event.type = "IssueEvent"
        issue_event.repo.name = "testuser/repo3"
        events.append(issue_event)
        
        # Pull request review event
        review_event = Mock()
        review_event.type = "PullRequestReviewEvent"
        review_event.repo.name = "testuser/repo1"
        events.append(review_event)
        
        # Unknown event type
        unknown_event = Mock()
        unknown_event.type = "UnknownEvent"
        unknown_event.repo.name = "testuser/repo4"
        events.append(unknown_event)
        
        return events

    def test_init_with_token(self):
        """Test ActivityTracker initialization with token."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_user = Mock(spec=AuthenticatedUser)
            mock_user.login = "testuser"
            mock_github.get_user.return_value = mock_user
            
            tracker = ActivityTracker("testuser", "test_token")
            
            # Check that Github was called with the correct parameters
            mock_github_class.assert_called_once()
            call_args = mock_github_class.call_args
            assert call_args is not None
            assert 'auth' in call_args.kwargs
            assert call_args.kwargs['auth'].token == "test_token"
            assert call_args.kwargs['per_page'] == 100
            assert tracker.username == "testuser"
            assert tracker.token == "test_token"

    def test_init_without_token_uses_env_var(self):
        """Test ActivityTracker initialization without token uses environment variable."""
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token'}):
            with patch('activity_tracker.Github') as mock_github_class:
                mock_github = Mock()
                mock_github_class.return_value = mock_github
                
                mock_user = Mock(spec=AuthenticatedUser)
                mock_user.login = "testuser"
                mock_github.get_user.return_value = mock_user
                
                tracker = ActivityTracker("testuser")
                
                # Check that Github was called with the correct parameters
                mock_github_class.assert_called_once()
                call_args = mock_github_class.call_args
                assert call_args is not None
                assert 'auth' in call_args.kwargs
                assert call_args.kwargs['auth'].token == "env_token"
                assert call_args.kwargs['per_page'] == 100
                assert tracker.token == "env_token"

    def test_init_without_token_no_env_var(self):
        """Test ActivityTracker initialization without token and no environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('activity_tracker.Github') as mock_github_class:
                mock_github = Mock()
                mock_github_class.return_value = mock_github
                
                mock_user = Mock(spec=AuthenticatedUser)
                mock_user.login = "testuser"
                mock_github.get_user.return_value = mock_user
                
                tracker = ActivityTracker("testuser")
                
                mock_github_class.assert_called_once_with(per_page=100)
                assert tracker.token is None

    def test_init_github_exception_401(self):
        """Test initialization with invalid token (401 error)."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            # Simulate 401 Unauthorized error
            mock_github.get_user.side_effect = GithubException(
                status=401, data={"message": "Bad credentials"}
            )
            
            with pytest.raises(ValueError, match="Invalid GitHub token"):
                ActivityTracker("testuser", "invalid_token")

    def test_init_github_exception_403(self):
        """Test initialization with rate limit exceeded (403 error)."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            # Simulate 403 Forbidden error
            mock_github.get_user.side_effect = GithubException(
                status=403, data={"message": "API rate limit exceeded"}
            )
            
            with pytest.raises(ValueError, match="GitHub API rate limit exceeded"):
                ActivityTracker("testuser", "test_token")

    def test_init_github_exception_other(self):
        """Test initialization with other GitHub API errors."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            # Simulate 500 Internal Server Error
            mock_github.get_user.side_effect = GithubException(
                status=500, data={"message": "Internal server error"}
            )
            
            with pytest.raises(ConnectionError, match="Failed to connect to GitHub API"):
                ActivityTracker("testuser", "test_token")

    def test_init_unexpected_exception(self):
        """Test initialization with unexpected exceptions."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            # Simulate unexpected exception
            mock_github.get_user.side_effect = Exception("Network error")
            
            with pytest.raises(ConnectionError, match="Unexpected error connecting to GitHub"):
                ActivityTracker("testuser", "test_token")

    def test_get_user_event_activity_authenticated_user(self, mock_authenticated_user, sample_events):
        """Test getting event activity for authenticated user."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            mock_github.get_user.return_value = mock_authenticated_user
            
            # Mock the events
            mock_events = Mock()
            mock_events.__iter__ = lambda self: iter(sample_events)
            mock_authenticated_user.get_events.return_value = mock_events
            
            tracker = ActivityTracker("testuser", "test_token")
            result = tracker.get_user_event_activity()
            
            # Verify the result structure
            assert 'stats' in result
            assert len(result['stats']) == 4  # 4 unique repositories
            
            # Find repo1 stats
            repo1_stats = next((s for s in result['stats'] if s['name'] == 'testuser/repo1'), None)
            assert repo1_stats is not None
            assert repo1_stats['counter']['pushes'] == 1
            assert repo1_stats['counter']['pull_requests'] == 1
            assert repo1_stats['counter']['pull_request_reviews'] == 1
            assert repo1_stats['owned'] == True
            
            # Find repo2 stats
            repo2_stats = next((s for s in result['stats'] if s['name'] == 'otheruser/repo2'), None)
            assert repo2_stats is not None
            assert repo2_stats['counter']['issue_comments'] == 1
            assert repo2_stats['owned'] == False

    def test_get_user_event_activity_named_user(self, mock_named_user, sample_events):
        """Test getting event activity for named user (public events only)."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            mock_github.get_user.return_value = mock_named_user
            
            # Mock the events
            mock_events = Mock()
            mock_events.__iter__ = lambda self: iter(sample_events)
            mock_named_user.get_public_events.return_value = mock_events
            
            tracker = ActivityTracker("testuser", "test_token")
            result = tracker.get_user_event_activity()
            
            # Verify that get_public_events was called instead of get_events
            mock_named_user.get_public_events.assert_called_once()
            mock_named_user.get_events.assert_not_called()

    def test_get_user_event_activity_no_connection(self):
        """Test getting event activity without established connection."""
        tracker = ActivityTracker.__new__(ActivityTracker)
        tracker.github = None
        tracker.user = None
        
        with pytest.raises(RuntimeError, match="GitHub connection not established"):
            tracker.get_user_event_activity()

    def test_get_rate_limit_info(self):
        """Test getting rate limit information."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_user = Mock(spec=AuthenticatedUser)
            mock_user.login = "testuser"
            mock_github.get_user.return_value = mock_user
            
            # Mock rate limit response
            mock_rate_limit = Mock()
            mock_rate_limit.core.limit = 5000
            mock_rate_limit.core.remaining = 4500
            mock_rate_limit.core.reset = None
            mock_rate_limit.search.limit = 30
            mock_rate_limit.search.remaining = 25
            mock_github.get_rate_limit.return_value = mock_rate_limit
            
            tracker = ActivityTracker("testuser", "test_token")
            result = tracker.get_rate_limit_info()
            
            assert result['limit'] == 5000
            assert result['remaining'] == 4500
            assert result['reset_time'] is None
            assert result['search_limit'] == 30
            assert result['search_remaining'] == 25

    def test_get_rate_limit_info_no_connection(self):
        """Test getting rate limit info without established connection."""
        tracker = ActivityTracker.__new__(ActivityTracker)
        tracker.github = None
        
        with pytest.raises(RuntimeError, match="GitHub connection not established"):
            tracker.get_rate_limit_info()

    def test_get_rate_limit_info_github_exception(self):
        """Test getting rate limit info with GitHub API error."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_user = Mock(spec=AuthenticatedUser)
            mock_user.login = "testuser"
            mock_github.get_user.return_value = mock_user
            
            # Simulate GitHub API error
            mock_github.get_rate_limit.side_effect = GithubException(
                status=500, data={"message": "Internal server error"}
            )
            
            tracker = ActivityTracker("testuser", "test_token")
            
            with pytest.raises(RuntimeError, match="Failed to fetch rate limit info"):
                tracker.get_rate_limit_info()

    def test_close(self):
        """Test closing the GitHub connection."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_user = Mock(spec=AuthenticatedUser)
            mock_user.login = "testuser"
            mock_github.get_user.return_value = mock_user
            
            tracker = ActivityTracker("testuser", "test_token")
            
            # Verify initial state
            assert tracker.github is not None
            assert tracker.user is not None
            
            # Close the connection
            tracker.close()
            
            # Verify final state
            assert tracker.github is None
            assert tracker.user is None
            mock_github.close.assert_called_once()

    def test_context_manager(self):
        """Test ActivityTracker as a context manager."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_user = Mock(spec=AuthenticatedUser)
            mock_user.login = "testuser"
            mock_github.get_user.return_value = mock_user
            
            with ActivityTracker("testuser", "test_token") as tracker:
                assert tracker.github is not None
                assert tracker.user is not None
            
            # Connection should be closed after exiting context
            assert tracker.github is None
            assert tracker.user is None
            mock_github.close.assert_called_once()

    def test_event_type_mapping(self):
        """Test that all event types are properly mapped to counters."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_user = Mock(spec=AuthenticatedUser)
            mock_user.login = "testuser"
            mock_github.get_user.return_value = mock_user
            
            # Create events for all supported types
            events = []
            event_types = [
                "PushEvent", "PullRequestEvent", "IssueCommentEvent", 
                "IssueEvent", "PullRequestReviewCommentEvent", "PullRequestReviewEvent"
            ]
            
            for event_type in event_types:
                event = Mock()
                event.type = event_type
                event.repo.name = "testuser/testrepo"
                events.append(event)
            
            # Mock the events
            mock_events = Mock()
            mock_events.__iter__ = lambda self: iter(events)
            mock_user.get_events.return_value = mock_events
            
            tracker = ActivityTracker("testuser", "test_token")
            result = tracker.get_user_event_activity()
            
            # Verify all event types are counted
            repo_stats = result['stats'][0]
            assert repo_stats['counter']['pushes'] == 1
            assert repo_stats['counter']['pull_requests'] == 1
            assert repo_stats['counter']['issue_comments'] == 1
            assert repo_stats['counter']['issues'] == 1
            assert repo_stats['counter']['pull_request_comments'] == 1
            assert repo_stats['counter']['pull_request_reviews'] == 1

    def test_owned_repository_detection(self):
        """Test detection of owned vs non-owned repositories."""
        with patch('activity_tracker.Github') as mock_github_class:
            mock_github = Mock()
            mock_github_class.return_value = mock_github
            
            mock_user = Mock(spec=AuthenticatedUser)
            mock_user.login = "testuser"
            mock_github.get_user.return_value = mock_user
            
            # Create events for owned and non-owned repos
            events = []
            
            # Owned repo (case insensitive)
            owned_event = Mock()
            owned_event.type = "PushEvent"
            owned_event.repo.name = "TestUser/owned-repo"
            events.append(owned_event)
            
            # Non-owned repo
            non_owned_event = Mock()
            non_owned_event.type = "PushEvent"
            non_owned_event.repo.name = "otheruser/non-owned-repo"
            events.append(non_owned_event)
            
            # Mock the events
            mock_events = Mock()
            mock_events.__iter__ = lambda self: iter(events)
            mock_user.get_events.return_value = mock_events
            
            tracker = ActivityTracker("testuser", "test_token")
            result = tracker.get_user_event_activity()
            
            # Verify owned status
            owned_repo = next((s for s in result['stats'] if s['name'] == 'TestUser/owned-repo'), None)
            non_owned_repo = next((s for s in result['stats'] if s['name'] == 'otheruser/non-owned-repo'), None)
            
            assert owned_repo is not None
            assert non_owned_repo is not None
            assert owned_repo['owned'] == True
            assert non_owned_repo['owned'] == False


if __name__ == "__main__":
    pytest.main([__file__]) 