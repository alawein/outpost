from app import get_user


def test_get_user_returns_the_given_id():
    assert get_user(7)["id"] == 7
