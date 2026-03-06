import grpc
from concurrent import futures
import os
import re
import time

from google import genai

import hashtagging_pb2
import hashtagging_pb2_grpc

# Configure Gemini
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
MODEL = "gemini-2.0-flash"


def _fallback_hashtag(post_content):
    """Generate a simple hashtag from post content when the API fails."""
    stop_words = {
        "i", "me", "my", "the", "a", "an", "is", "was", "are", "be", "been",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "it",
        "this", "that", "so", "and", "or", "but", "not", "just", "out",
        "up", "has", "had", "have", "do", "did", "all", "its", "our",
    }
    words = re.findall(r"[a-zA-Z]+", post_content)
    for word in words:
        if len(word) > 3 and word.lower() not in stop_words:
            return "#" + word.capitalize()
    return "#Post"


def generate_hashtag(post_content):
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=(
                    "Generate a single relevant hashtag for the following social media post. "
                    "Reply with ONLY the hashtag (e.g. #vacation). No explanation, no extra text, "
                    "just one hashtag.\n\n"
                    f"Post: {post_content}"
                ),
            )
            hashtag = response.text.strip()
            # Ensure it starts with # and is a single token
            if not hashtag.startswith("#"):
                hashtag = "#" + hashtag
            # Take only the first hashtag if multiple were returned
            hashtag = hashtag.split()[0]
            return hashtag
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return _fallback_hashtag(post_content)


class HashtagServiceServicer(hashtagging_pb2_grpc.HashtagServiceServicer):
    def GetHashtag(self, request, context):
        hashtag = generate_hashtag(request.post_content)
        return hashtagging_pb2.HashtagResponse(hashtag=hashtag)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    hashtagging_pb2_grpc.add_HashtagServiceServicer_to_server(
        HashtagServiceServicer(), server
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Hashtagging gRPC service running on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
