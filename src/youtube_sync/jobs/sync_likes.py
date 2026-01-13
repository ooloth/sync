import argparse

from youtube_sync.logging import get_logger, setup_logging

log = get_logger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Sync YouTube liked videos to Notion",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed debug output",
    )
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)

    log.info("sync started", sync_type="likes")
    log.warning("not yet implemented - coming soon!")
    log.info("sync complete", videos_synced=0)


if __name__ == "__main__":
    main()
