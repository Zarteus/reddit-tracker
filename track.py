import json
import re
import urllib.request
import os

POST_URL = "https://old.reddit.com/r/TELUSinternational/comments/1uitcbl/nta_no_tasks_available_weekly_thread_create_all/.json"
KEYWORD_PATTERN = re.compile(r"\buk\b", re.IGNORECASE)
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
SEEN_FILE = "seen.json"

HEADERS = {"User-Agent": "python:reddit-comment-tracker:v1.0 (by /u/Zarteus_1)"}

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def walk_comments(children, out):
    for child in children:
        if child.get("kind") != "t1":
            continue
        data = child["data"]
        out.append(data)
        replies = data.get("replies")
        if isinstance(replies, dict):
            walk_comments(replies["data"]["children"], out)

def send_discord(message):
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req)

def main():
    seen = load_seen()
    data = fetch_json(POST_URL)
    comments = []
    walk_comments(data[1]["data"]["children"], comments)

    new_matches = 0
    for c in comments:
        cid = c.get("id")
        body = c.get("body", "")
        if not cid or cid in seen:
            continue
        if KEYWORD_PATTERN.search(body):
            author = c.get("author", "unknown")
            permalink = "https://www.reddit.com" + c.get("permalink", "")
            excerpt = body[:300]
            message = f"**New matching comment by u/{author}**\n{excerpt}\n{permalink}"
            send_discord(message)
            seen.add(cid)
            new_matches += 1

    save_seen(seen)
    print(f"Checked {len(comments)} comments, sent {new_matches} alert(s).")

if __name__ == "__main__":
    main()
