import src.youtube_sync.io.notion.bookmarks as notion
import src.youtube_sync.io.youtube.likes as youtube
from src.new_folder_layout_2.domain.bookmarks.core.decisions import (
    BookmarksToAddDecision,
    choose_bookmarks_to_add,
)


def invariant(condition: bool, message: str | None):
    """Assert that a condition holds true, otherwise raise an AssertionError with the provided message."""
    if not condition:
        raise AssertionError(message or str(condition))


def orchestrate_bookmarks_sync():
    print("Orchestrating bookmark operations...")
    # Here you would call functions from decisions.py and other modules
    # to manage bookmarks based on the application's requirements.

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
