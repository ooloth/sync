from dataclasses import dataclass
from enum import StrEnum


class BookmarksToAddDecision(StrEnum):
    ADD_BOOKMARKS = "add_bookmarks"
    NO_ACTION_NEEDED = "no_action_needed"


@dataclass(frozen=True, slots=True)
class BookmarksToAddResult:
    decision: BookmarksToAddDecision
    bookmarks_to_add: set | None


def bookmarks_to_add(
    current_bookmark_urls: set[str],
    desired_bookmark_urls: set,
) -> BookmarksToAddResult:
    """
    Determine which bookmarks need to be added.

    Returns:
        BookmarksToAddResult: The result containing the decision and bookmarks to add (if any).

    Example:
        current = {"http://example.com/a", "http://example.com/b"}
        desired = {"http://example.com/a", "http://example.com/c"}
        result = bookmarks_to_add(current, desired)

        match result.decision:
            case BookmarksToAddDecision.ADD_BOOKMARKS:
                print("Bookmarks to add:", result.bookmarks_to_add)
            case BookmarksToAddDecision.NO_ACTION_NEEDED:
                print("No action needed.")
    """
    new_bookmarks = desired_bookmark_urls - current_bookmark_urls

    if not new_bookmarks:
        return BookmarksToAddResult(
            decision=BookmarksToAddDecision.NO_ACTION_NEEDED,
            bookmarks_to_add=None,
        )

    return BookmarksToAddResult(
        decision=BookmarksToAddDecision.ADD_BOOKMARKS,
        bookmarks_to_add=new_bookmarks,
    )
