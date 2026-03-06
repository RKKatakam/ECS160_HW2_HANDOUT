import grpc
from concurrent import futures
import os

from google import genai

import hashtagging_pb2
import hashtagging_pb2_grpc

# Configure Gemini
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
MODEL = "gemini-2.0-flash"


def generate_hashtag(post_content):
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
        return "#bskypost"


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
