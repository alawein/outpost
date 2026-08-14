def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "demo"}


def create_order(user_id: int, item: str) -> dict:
    return {"user_id": user_id, "item": item, "status": "pending"}
