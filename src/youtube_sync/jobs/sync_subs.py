import argparse

import rich
from result import Err, Ok

from youtube_sync.io.feedbin import create_client as create_feedbin_client
from youtube_sync.io.youtube import create_client as create_youtube_client


def main():
    parser = argparse.ArgumentParser(
        description="Sync YouTube subscriptions to Feedbin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
By default, this runs in DRY-RUN mode and shows what would be created.
Use --apply to actually create subscriptions in Feedbin.
        """,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create subscriptions (default is dry-run)",
    )
    args = parser.parse_args()

    if args.apply:
        rich.print("[bold yellow]⚠️  APPLY MODE - will make real changes[/bold yellow]")
    else:
        rich.print("[bold cyan]🔍 DRY-RUN MODE - no changes will be made[/bold cyan]")

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

    # Build YouTube feed URLs
    yt_feed_urls = set()
    for sub in yt_subs:
        channel_id = sub.snippet.resource_id.channel_id
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        yt_feed_urls.add(feed_url)

    # Build existing Feedbin feed URLs
    fb_feed_urls = {str(sub.feed_url) for sub in fb_subs}

    # Find feeds that need to be created
    feeds_to_create = yt_feed_urls - fb_feed_urls

    rich.print("\n[bold]Analysis:[/bold]")
    rich.print(f"  YouTube feeds: {len(yt_feed_urls)}")
    rich.print(f"  Feedbin feeds: {len(fb_feed_urls)}")
    rich.print(f"  Feeds to create: {len(feeds_to_create)}")

    if not feeds_to_create:
        rich.print("\n[green]✓ All YouTube subscriptions already exist in Feedbin![/green]")
        return

    # Show which channels will be created
    rich.print("\n[bold]Channels to create in Feedbin:[/bold]")
    for feed_url in sorted(feeds_to_create):
        # Find the channel name from YouTube subs
        channel_id = feed_url.split("channel_id=")[1]
        matching_sub = next(
            (s for s in yt_subs if s.snippet.resource_id.channel_id == channel_id),
            None,
        )
        channel_name = (
            matching_sub.snippet.channel_title or matching_sub.snippet.title
            if matching_sub
            else "Unknown"
        )

        if args.apply:
            result = feedbin.create_subscription(feed_url)
            match result:
                case Ok(_):
                    rich.print(f"  ✓ Created: {channel_name}")
                case Err(error):
                    rich.print(f"  [red]✗ Failed to create {channel_name}: {error}[/red]")
        else:
            rich.print(f"  [dim]• {channel_name}[/dim]")
            rich.print(f"    [dim]{feed_url}[/dim]")

    if not args.apply:
        rich.print("\n[yellow]═══════════════════════════════════════════════[/yellow]")
        rich.print("[yellow]DRY RUN - no changes were made to Feedbin[/yellow]")
        rich.print(
            f"[yellow]Run with --apply to create {len(feeds_to_create)} subscription(s)[/yellow]"
        )
        rich.print("[yellow]═══════════════════════════════════════════════[/yellow]")
    else:
        rich.print("\n[green]✓ Sync complete![/green]")


if __name__ == "__main__":
    main()
