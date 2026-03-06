import os
import pytest
from unittest.mock import patch, MagicMock

# Set a dummy key before importing the module so genai.Client doesn't fail
os.environ.setdefault("GOOGLE_API_KEY", "test-key")

with patch("google.genai.Client"):
    from hashtagging_service import generate_hashtag, HashtagServiceServicer
    import hashtagging_pb2


@patch("hashtagging_service.client")
def test_generate_hashtag_returns_hashtag(mock_client):
    mock_response = MagicMock()
    mock_response.text = "#vacation"
    mock_client.models.generate_content.return_value = mock_response

    result = generate_hashtag("Just had an amazing trip to Hawaii!")
    assert result == "#vacation"
    mock_client.models.generate_content.assert_called_once()


@patch("hashtagging_service.client")
def test_generate_hashtag_adds_hash_prefix(mock_client):
    mock_response = MagicMock()
    mock_response.text = "cooking"
    mock_client.models.generate_content.return_value = mock_response

    result = generate_hashtag("Made a great meal today")
    assert result == "#cooking"


@patch("hashtagging_service.client")
def test_generate_hashtag_fallback_on_error(mock_client):
    mock_client.models.generate_content.side_effect = Exception("API error")

    result = generate_hashtag("Some post content")
    assert result == "#bskypost"


@patch("hashtagging_service.client")
def test_generate_hashtag_takes_first_token(mock_client):
    mock_response = MagicMock()
    mock_response.text = "#food #cooking #yummy"
    mock_client.models.generate_content.return_value = mock_response

    result = generate_hashtag("Made pasta today")
    assert result == "#food"


@patch("hashtagging_service.generate_hashtag")
def test_servicer_get_hashtag(mock_generate):
    mock_generate.return_value = "#sunset"
    servicer = HashtagServiceServicer()
    request = hashtagging_pb2.HashtagRequest(post_content="Beautiful sunset!")
    context = MagicMock()

    response = servicer.GetHashtag(request, context)
    assert response.hashtag == "#sunset"
    mock_generate.assert_called_once_with("Beautiful sunset!")
