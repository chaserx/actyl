from activity_tracker import ActivityTracker
from rich.console import Console
from rich.table import Table
import argparse

def main():
    """Main function to demonstrate the ActivityTracker usage."""
    print("Welcome to Actyl - GitHub Activity Tracker!")

    # Get the username from the command line
    parser = argparse.ArgumentParser(description="GitHub Activity Tracker")
    parser.add_argument("-u", "--usernames", nargs="+", help="GitHub usernames")
    args = parser.parse_args()
    usernames = args.usernames

    for username in usernames:
        try:
            # Initialize the activity tracker
            with ActivityTracker(username=username) as tracker:
                console = Console()

                # Get User Activity
                user_activity = tracker.get_user_event_activity()
                print("\n🔗 Connected to GitHub successfully!")
                print(f"\n🔍 Most common event types for {username}:")
                print_user_activity(console, user_activity)

                # Display rate limit information
                rate_limit_info = tracker.get_rate_limit_info()
                print_rate_usage(console, rate_limit_info)
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
        except ConnectionError as e:
            print(f"❌ Connection error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def print_user_activity(console, user_activity, depth=3):
    activity_table = Table(title="")
    activity_table.add_column("Repository", justify="right", style="cyan", no_wrap=True)
    activity_table.add_column("Event type", justify="right", style="cyan", no_wrap=True)
    activity_table.add_column("Count", justify="right", style="magenta", no_wrap=True)
    for repo_stats in user_activity['stats']:
        for event_type, count in repo_stats['counter'].most_common(depth):
            activity_table.add_row(f"{repo_stats['name']} ({'owned' if repo_stats['owned'] else 'not owned'})", event_type, str(count))
    console.print(activity_table)

def print_rate_usage(console, rate_limit_info):
    print("\n⚠️ Rate limit info:")
    usage_table = Table(title="")
    usage_table.add_column("Usage", justify="right", style="cyan", no_wrap=True)
    usage_table.add_column("Limit", justify="right", style="magenta", no_wrap=True)
    usage_table.add_column("Remaining", justify="right", style="green", no_wrap=True)
    usage_table.add_row(str(rate_limit_info['limit']), str(rate_limit_info['remaining']), str(rate_limit_info['reset_time']))
    console.print(usage_table)

if __name__ == "__main__":
    main()
