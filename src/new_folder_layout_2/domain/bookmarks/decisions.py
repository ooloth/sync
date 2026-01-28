def bookmarks_to_add(current_bookmarks: set, desired_bookmarks: set) -> set:
    """Determine which bookmarks need to be added.

    Args:
        current_bookmarks (set): A set of current bookmark URLs.
        desired_bookmarks (set): A set of desired bookmark URLs.

    Returns:
        set: A set of bookmark URLs that need to be added.
    """
    return desired_bookmarks - current_bookmarks
