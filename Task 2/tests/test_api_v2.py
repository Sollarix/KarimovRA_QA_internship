import pytest
import requests
from utils import generate_test_item


class TestAPIv2:
    BASE_PATH = "/api/2"

    def _create_and_get_id(self, base_url, api_client) -> str:
        payload = generate_test_item()
        resp = api_client.post(f"{base_url}/api/1/item", json=payload)
        assert resp.status_code == 200
        return resp.json()["status"].split(" - ")[1]

    def test_pos_delete_item_success(self, base_url, api_client):
        """TC-INT-001: Успешное удаление → 200"""
        item_id = self._create_and_get_id(base_url, api_client)
        response = api_client.delete(f"{base_url}{self.BASE_PATH}/item/{item_id}")
        assert response.status_code == 200
        assert response.text == ""  # пустое тело

    def test_neg_delete_nonexistent_item(self, base_url, api_client):
        """TC-INT-001: Удаление несуществующего → 404, но status='500' в теле"""
        fake_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
        response = api_client.delete(f"{base_url}{self.BASE_PATH}/item/{fake_id}")
        assert response.status_code == 404
        data = response.json()

        status_in_body = data.get("status")
        if status_in_body == "500":
            pytest.fail(f"HTTP 404, но в теле status='500'. Тело: {data}")
        assert status_in_body == "404", f"Ожидалось '404' в поле status, получено: {status_in_body}"