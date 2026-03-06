import csv
import requests
import sys


def load_posts(input_path):
    posts = []
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["like_count"] = int(row["like_count"])
            row["reply_count"] = int(row["reply_count"])
            posts.append(row)
    return posts


def get_top_posts(posts, limit=10):
    sorted_posts = sorted(posts, key=lambda p: p["like_count"], reverse=True)
    return sorted_posts[:limit]


def send_to_pipeline(post_content):
    """
    Send a post to the moderation service.
    Returns the hashtag string on success, or 'FAILED' if moderation fails.
    """
    try:
        response = requests.post(
            "http://localhost:8001/moderate",
            json={"post_content": post_content},
            timeout=30,
        )
        data = response.json()
        return data["result"]
    except Exception:
        return "FAILED"


def process_post(post, index):
    result = send_to_pipeline(post["text"])
    print(f"Post {index}:", flush=True)
    if result == "FAILED":
        print("[DELETED]", flush=True)
    else:
        print(f"{post['text']} {result}", flush=True)
    print(flush=True)


def main():
    input_path = sys.argv[1] if len(sys.argv) > 1 else "input.csv"

    posts = load_posts(input_path)
    top_posts = get_top_posts(posts, limit=10)

    print(f"Processing {len(top_posts)} most-liked posts...\n")

    for i, post in enumerate(top_posts, start=1):
        process_post(post, i)


if __name__ == "__main__":
    main()
