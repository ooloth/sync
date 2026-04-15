import argparse

from result import Err, Ok

from sync.io.feedbin import create_client as create_feedbin_client
from sync.io.youtube import create_client as create_youtube_client
from sync.logging import get_logger, setup_logging

log = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Sync YouTube subscriptions to Feedbin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
By default, this runs in DRY-RUN mode and shows what would be created.
Use --apply to actually create subscriptions in Feedbin.
Use --verbose to see detailed debug output.
        """,
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually create subscriptions (default is dry-run)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed debug output",
    )
    args = parser.parse_args()

    # Configure logging based on verbosity
    setup_logging(verbose=args.verbose, job_name="sync_subs")

    if args.apply:
        log.warning("APPLY MODE - will make real changes", mode="apply")
    else:
        log.info("DRY-RUN MODE - no changes will be made", mode="dry_run")

    log.info("fetching YouTube subscriptions")
    youtube = create_youtube_client()
    yt_result = youtube.list_subscriptions()

    match yt_result:
        case Err(error):
            log.error("failed to fetch YouTube subscriptions", error=error)
            return
        case Ok(yt_subs):
            yt_count = len(yt_subs)
            log.info("fetched YouTube subscriptions", count=yt_count)

    log.info("fetching Feedbin subscriptions")
    feedbin = create_feedbin_client()
    fb_result = feedbin.list_subscriptions()

    match fb_result:
        case Err(error):
            log.error("failed to fetch Feedbin subscriptions", error=error)
            return
        case Ok(fb_subs):
            fb_count = len(fb_subs)
            log.info("fetched Feedbin subscriptions", count=fb_count)

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

    log.info(
        "analysis complete",
        youtube_feeds=len(yt_feed_urls),
        feedbin_feeds=len(fb_feed_urls),
        feeds_to_create=len(feeds_to_create),
    )

    if not feeds_to_create:
        log.info("all YouTube subscriptions already exist in Feedbin")
        return

    log.info("preparing to create subscriptions", count=len(feeds_to_create))
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
                    log.info("created subscription", channel=channel_name, url=feed_url)
                case Err(error):
                    log.error(
                        "failed to create subscription",
                        channel=channel_name,
                        url=feed_url,
                        error=error,
                    )
        else:
            log.info("would create subscription", channel=channel_name, url=feed_url)

    if not args.apply:
        log.warning(
            "DRY RUN complete - no changes were made",
            would_create=len(feeds_to_create),
        )
    else:
        log.info("sync complete", created=len(feeds_to_create))


if __name__ == "__main__":
    main()
