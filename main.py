from activity_tracker import ActivityTracker
from rich.console import Console
from rich.table import Table
import sys  

def main():
    """Main function to demonstrate the ActivityTracker usage."""
    print("Welcome to Actyl - GitHub Activity Tracker!")
    
    # Get the username from the command line
    username = sys.argv[1]

    try:
        # Initialize the activity tracker
        with ActivityTracker(username=username) as tracker:
            print("\n🔗 Connected to GitHub successfully!")
            
            # Get user event activity
            user_activity = tracker.get_user_event_activity()
            print(f"\n🔍 Most common event types for {username}:")
            
            console = Console()
            table = Table(title="")
            table.add_column("Repository", justify="right", style="cyan", no_wrap=True)
            table.add_column("Event type", justify="right", style="cyan", no_wrap=True)
            table.add_column("Count", justify="right", style="magenta", no_wrap=True)
            for repo_stats in user_activity['stats']:
                for event_type, count in repo_stats['counter'].most_common(3):
                    table.add_row(f"{repo_stats['name']} ({'owned' if repo_stats['owned'] else 'not owned'})", event_type, str(count))
            console.print(table)

            print(f"\n⚠️ Rate limit info:")
            limit_table = Table(title="")
            limit_table.add_column("Limit", justify="right", style="cyan", no_wrap=True)
            limit_table.add_column("Remaining", justify="right", style="magenta", no_wrap=True)
            limit_table.add_column("Reset at", justify="right", style="green", no_wrap=True)
            limit_table.add_row(str(tracker.get_rate_limit_info()['limit']), str(tracker.get_rate_limit_info()['remaining']), str(tracker.get_rate_limit_info()['reset_time']))
            console.print(limit_table)
    
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
    