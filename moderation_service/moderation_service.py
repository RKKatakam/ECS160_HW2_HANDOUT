from fastapi import FastAPI
from pydantic import BaseModel
import grpc

import hashtagging_pb2
import hashtagging_pb2_grpc

app = FastAPI()

BANNED_WORDS = [
    "illegal", "fraud", "scam", "exploit", "dox",
    "swatting", "hack", "crypto", "bots",
]


class ModerateRequest(BaseModel):
    post_content: str


class ModerateResponse(BaseModel):
    result: str


def check_moderation(text):
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return False
    return True


def get_hashtag_from_service(post_content):
    channel = grpc.insecure_channel("localhost:50051")
    stub = hashtagging_pb2_grpc.HashtagServiceStub(channel)
    response = stub.GetHashtag(hashtagging_pb2.HashtagRequest(post_content=post_content))
    return response.hashtag


@app.post("/moderate")
def moderate(request: ModerateRequest):
    if not check_moderation(request.post_content):
        return {"result": "FAILED"}
    hashtag = get_hashtag_from_service(request.post_content)
    return {"result": hashtag}
