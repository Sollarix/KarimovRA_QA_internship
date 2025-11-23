import re
import uuid
from typing import Dict, Any


def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(val)
        return True
    except ValueError:
        return False


def generate_test_item(seller_id: int = 111121, name: str = "Тестовое объявление",
                       price: int = 1000,
                       likes: int = 5, view_count: int = 50, contacts: int = 2) -> Dict[str, Any]:
    return {
        "sellerID": seller_id,
        "name": name,
        "price": price,
        "statistics": {
            "likes": likes,
            "viewCount": view_count,
            "contacts": contacts
        }
    }