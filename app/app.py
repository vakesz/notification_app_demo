import argparse
import json
import threading
import time

# ── Imports
from flask import Flask, jsonify, render_template

# ── Parse the interval from CLI
parser = argparse.ArgumentParser()
parser.add_argument(
    "--add_post_interval",
    type=int,
    default=30,
    help="Seconds between adding a new post"
)
args = parser.parse_args()

app = Flask(__name__)

# ── Load your queued posts
with open("app/posts_list.txt", "r", encoding="utf-8") as f:
    queued_posts = json.load(f)

lock = threading.Lock()
pending_posts = []   # HTML snippets to inject

def scheduler():
    """Background thread: every interval, pop a post and render its HTML."""
    counter = 0
    while queued_posts:
        time.sleep(args.add_post_interval)
        post = queued_posts.pop(0)
        counter += 1
        # render the Jinja partial for this post
        html = render_template(
            "post.html",
            post=post,
            block_id=f"dynamic-block-{counter}"
        )
        with lock:
            pending_posts.insert(0, html)

# start in background
threading.Thread(target=scheduler, daemon=True).start()

@app.route("/")
def index():
    # pass interval (ms) into JS
    return render_template(
        "index.html",
        interval_ms=args.add_post_interval * 1000
    )

@app.route("/new_posts")
def new_posts():
    """AJAX endpoint: return any newly-scheduled posts."""
    with lock:
        posts_to_send = pending_posts.copy()
        pending_posts.clear()
    return jsonify(posts=posts_to_send)

if __name__ == "__main__":
    app.run(debug=True)

def main():
    """Entry point for the console script."""
    app.run(debug=True)
