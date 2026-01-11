import rich

from youtube_sync.io.feedbin.client import create_client


def main():
    rich.print("Syncing YouTube subscriptions to Feedbin...")

    rich.print("Fetching Feedbin subscriptions")
    feedbin = create_client()
    subs = feedbin.list_subscriptions()

    count = len(subs)
    rich.print(f"Total subscriptions: {count}")


if __name__ == "__main__":
    main()
