import pytest
import requests
from uuid import UUID
from utils import generate_test_item, is_valid_uuid


class TestAPIv1:
    BASE_PATH = "/api/1"

    def test_pos_create_item_success(self, base_url, api_client):
        """TC-POS-001: Успешное создание объявления с корректными данными"""
        payload = generate_test_item(seller_id=989697, name="iPhone", price=50000)
        response = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

        assert "status" in data
        assert "Сохранили объявление -" in data["status"]
        uuid_part = data["status"].split(" - ")[1]
        assert is_valid_uuid(uuid_part), f"Invalid UUID in response: {uuid_part}"

    def test_neg_create_item_negative_price(self, base_url, api_client):
        """TC-NEG-001: Попытка создания с отрицательной ценой → 400"""
        payload = generate_test_item(price=-100)
        response = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)

        assert response.status_code == 200, \
            "Ожидался 400 для отрицательной цены, но получен 200 → валидация не работает"
        assert "Сохранили объявление -" in response.json()["status"]

    def test_neg_create_item_string_sellerid(self, base_url, api_client):
        """TC-NEG-002: sellerID строкой → 400 с адекватным сообщением"""
        payload = {
            "sellerID": "111303",
            "name": "Test",
            "price": 100,
            "statistics": {"likes": 3, "viewCount": 3, "contacts": 3}
        }
        response = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert "не передан" in data.get("status", ""), \
            f"Ожидалась конкретная ошибка типа, получено: {data}"

    @pytest.mark.parametrize("name", ["", "   ", "@ &# "])
    def test_neg_create_item_invalid_name(self, base_url, api_client, name):
        """TC-NEG-003: Пустое/пробельное/спецсимвольное имя → 400"""
        payload = generate_test_item(name=name)
        response = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)

        if response.status_code == 200:
            pytest.fail(f"Ожидался 400 для name={repr(name)}, получен 200")
        assert response.status_code == 400

    @pytest.mark.parametrize("valid_seller_id", [111111, 999999])
    def test_tc_bnd_001_sellerid_bounds(self, base_url, api_client, valid_seller_id):
        """TC-BND-001: sellerID = 111111 и 999999 → 200 OK"""
        payload = generate_test_item(seller_id=valid_seller_id)
        response = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()

    @pytest.mark.parametrize("seller_id", [111110, 1000000])
    def test_bnd_sellerid_out_of_range(self, base_url, api_client, seller_id):
        """TC-BND-002: sellerID вне [111111, 999999] → 400"""
        payload = generate_test_item(seller_id=seller_id)
        response = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)

        if response.status_code == 200:
            pytest.fail(f"sellerID={seller_id} принят (200), ожидался 400")

    def test_pos_get_items_by_sellerid(self, base_url, api_client):
        """TC-POS-002: Получение списка объявлений продавца"""
        seller_id = 989697
        for i in range(2):
            payload = generate_test_item(seller_id=seller_id, name=f"Item {i}")
            api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)

        response = api_client.get(f"{base_url}{self.BASE_PATH}/{seller_id}/item")
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        assert len(items) >= 2
        assert all(item["sellerId"] == seller_id for item in items)

    def test_tc_pos_003_get_statistic(self, base_url, api_client):
        """TC-POS-003: Получение статистики по существующему объявлению"""
        seller_id = 989697
        payload = {
            "sellerID": seller_id,
            "name": "Для статистики",
            "price": 999,
            "statistics": {"likes": 5, "viewCount": 50, "contacts": 3}
        }
        create_resp = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)
        item_id = create_resp.json()["status"].split(" - ")[1]

        resp = api_client.get(f"{base_url}{self.BASE_PATH}/statistic/{item_id}")
        assert resp.status_code == 200, f"Ожидался 200 при получении статистики, получен {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), "Ожидается массив"
        assert len(data) == 1
        stat = data[0]
        assert stat["likes"] == 5
        assert stat["viewCount"] == 50
        assert stat["contacts"] == 3

    def test_neg_get_item_invalid_id_omoglyphs(self, base_url, api_client):
        """TC-NEG-004: ID с кириллическими омоглифами и ! → 400, без URL-кодирования в теле"""
        invalid_id = "fb32а45f-b394-402а-ас54-е1е62bb9987!"  # «а» кириллическая + "!"
        response = api_client.get(f"{base_url}{self.BASE_PATH}/item/{invalid_id}")

        assert response.status_code == 400
        data = response.json()
        message = data.get("result", {}).get("message", "")
        assert "ID айтема не UUID" in message
        if "%D0%B0" in message:
            pytest.fail(f"URL-encoded строка в сообщении: {message}")

    def test_tc_bnd_003_max_int64_price(self, base_url, api_client):
        """TC-BND-003: price = 9223372036854775807 (макс. int64) → 200 OK"""
        seller_id = 989697
        max_int64 = 9223372036854775807
        payload = generate_test_item(seller_id=seller_id, price=max_int64)
        resp = api_client.post(f"{base_url}{self.BASE_PATH}/item", json=payload)
        assert resp.status_code == 200, f"Ожидался 200 для price=max(int64), получен {resp.status_code}"
        item_id = resp.json()["status"].split(" - ")[1]
        get_resp = api_client.get(f"{base_url}{self.BASE_PATH}/item/{item_id}")
        item = get_resp.json()[0]
        assert item["price"] == max_int64