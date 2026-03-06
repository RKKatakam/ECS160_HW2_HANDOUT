import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from moderation_service import app, check_moderation, BANNED_WORDS


client = TestClient(app)


def test_check_moderation_clean_post():
    assert check_moderation("What a beautiful sunny day!") is True


def test_check_moderation_banned_word():
    for word in BANNED_WORDS:
        assert check_moderation(f"This post contains {word}") is False


def test_check_moderation_case_insensitive():
    assert check_moderation("HACK the planet") is False
    assert check_moderation("Crypto is cool") is False


@patch("moderation_service.get_hashtag_from_service")
def test_moderate_endpoint_clean_post(mock_get_hashtag):
    mock_get_hashtag.return_value = "#sunshine"
    response = client.post("/moderate", json={"post_content": "What a sunny day!"})
    assert response.status_code == 200
    assert response.json()["result"] == "#sunshine"
    mock_get_hashtag.assert_called_once()


@patch("moderation_service.get_hashtag_from_service")
def test_moderate_endpoint_banned_post(mock_get_hashtag):
    response = client.post("/moderate", json={"post_content": "This is a scam!"})
    assert response.status_code == 200
    assert response.json()["result"] == "FAILED"
    mock_get_hashtag.assert_not_called()


@patch("moderation_service.get_hashtag_from_service")
def test_moderate_endpoint_returns_hashtag(mock_get_hashtag):
    mock_get_hashtag.return_value = "#hiking"
    response = client.post(
        "/moderate",
        json={"post_content": "Hiked to the top of the mountain!"},
    )
    assert response.status_code == 200
    result = response.json()["result"]
    assert result.startswith("#")
