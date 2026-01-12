import rich
from result import Err, Ok

from youtube_sync.io.feedbin import create_client as create_feedbin_client
from youtube_sync.io.youtube import create_client as create_youtube_client


def main():
    rich.print("Syncing YouTube subscriptions to Feedbin...")

    rich.print("\n[bold]Fetching YouTube subscriptions[/bold]")
    youtube = create_youtube_client()
    yt_result = youtube.list_subscriptions()

    match yt_result:
        case Err(error):
            rich.print(f"[red]Error:[/red] {error}")
            return
        case Ok(yt_subs):
            yt_count = len(yt_subs)
            rich.print(f"Total YouTube subscriptions: {yt_count}")

            # Show what YouTube subscriptions exist
            if yt_subs:
                rich.print("\n[bold]YouTube Channels:[/bold]")
                for sub in sorted(
                    yt_subs, key=lambda s: s.snippet.channel_title or s.snippet.title
                ):
                    channel_id = sub.snippet.resource_id.channel_id
                    channel_name = sub.snippet.channel_title or sub.snippet.title
                    rich.print(f"  • {channel_name} ({channel_id})")

    rich.print("\n[bold]Fetching Feedbin subscriptions[/bold]")
    feedbin = create_feedbin_client()
    fb_result = feedbin.list_subscriptions()

    match fb_result:
        case Err(error):
            rich.print(f"[red]Error:[/red] {error}")
            return
        case Ok(fb_subs):
            fb_count = len(fb_subs)
            rich.print(f"Total Feedbin subscriptions: {fb_count}")


if __name__ == "__main__":
    main()
