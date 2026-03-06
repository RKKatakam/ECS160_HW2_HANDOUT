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
MODEL = "gemini-2.5-flash"


def _fallback_hashtag(post_content):
    """
    ensures the returned tag looks like a single hashtag
    """
    default_tag = "#bskypost"
    
    if not post_content or not post_content.strip():
        return default_tag

    first_word = post_content.strip().split()[0]
    sanitized = "".join(ch for ch in first_word if ch.isalnum() or ch in "#_")
    
    tag = sanitized if sanitized.startswith("#") else "#" + sanitized
    
    return tag if len(tag) >= 2 and tag != "#" else default_tag



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
        except Exception as e:
            print(f"[Gemini ERROR] Attempt {attempt+1}/{max_retries}: {type(e).__name__}: {e}")
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
