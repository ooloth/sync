import argparse

import sync.io.notion.bookmarks as notion
import sync.io.youtube.likes as youtube
from sync.errors import invariant
from sync.logging import get_logger, setup_logging

from .core import BookmarksToAddDecision, choose_bookmarks_to_add

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

    setup_logging(verbose=args.verbose, job_name="sync_likes")

    log.info("sync started", sync_type="likes")
    print("Orchestrating bookmark operations...")

    # I/O
    current_bookmarks = notion.get_bookmarks()
    desired_bookmarks = youtube.get_likes()

    # Pure
    result = choose_bookmarks_to_add(current_bookmarks, desired_bookmarks)

    # I/O
    match result.decision:
        case BookmarksToAddDecision.ADD_BOOKMARKS:
            invariant(len(result.bookmarks_to_add) > 0, "Expected bookmarks to add, but got none.")
            for bookmark in result.bookmarks_to_add:
                notion.add_bookmark(bookmark)
                print(f"Added bookmark: {bookmark}")

        case BookmarksToAddDecision.NO_ACTION_NEEDED:
            invariant(
                len(result.bookmarks_to_add) == 0, "Expected no bookmarks to add, but got some."
            )
            print("No new bookmarks to add.")

    log.info("sync complete", videos_synced=0)


if __name__ == "__main__":
    main()
