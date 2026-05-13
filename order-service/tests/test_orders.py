# test_order.py — Unit tests for order-service
# Run with: python -m pytest tests/ -v --cov=. --cov-report=term
# Part of OrderFlow CI/CD pipeline

import pytest
from fastapi.testclient import TestClient

# ========================================
# Fixtures
# ========================================

@pytest.fixture
def client():
    """Create a test client for the order-service app."""
    from main import app, orders_db
    orders_db.clear()          # ← pulizia stato prima di ogni test
    return TestClient(app)

@pytest.fixture
def sample_order():
    """Sample order payload for testing."""
    return {
        "customer_name": "Mario Rossi",
        "items": [
            {"product_id": "PROD-001", "quantity": 2},
            {"product_id": "PROD-003", "quantity": 1}
        ]
    }

@pytest.fixture
def created_order(client, sample_order):
    """Crea un ordine e restituisce il JSON della risposta."""
    response = client.post("/api/orders", json=sample_order)
    assert response.status_code == 201
    return response.json()

# ========================================
# Health Check Tests
# ========================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_includes_service_name(self, client):
        data = client.get("/health").json()
        assert data["service"] == "order-service"

    def test_health_includes_version(self, client):
        data = client.get("/health").json()
        assert "version" in data

# ========================================
# Order CRUD Tests
# ========================================

class TestCreateOrder:
    def test_create_order_success(self, client, sample_order):
        response = client.post("/api/orders", json=sample_order)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] == "Mario Rossi"
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_order_returns_id(self, client, sample_order):
        data = client.post("/api/orders", json=sample_order).json()
        assert data["id"] is not None
        assert len(str(data["id"])) > 0

    def test_create_order_has_created_at(self, client, sample_order):
        data = client.post("/api/orders", json=sample_order).json()
        assert "created_at" in data

    def test_create_order_invalid_data(self, client):
        response = client.post("/api/orders", json={})
        assert response.status_code == 422

    def test_create_order_missing_items(self, client):
        response = client.post("/api/orders", json={"customer_name": "Test"})
        assert response.status_code == 422

    def test_create_order_empty_items(self, client):
        response = client.post("/api/orders", json={
            "customer_name": "Test",
            "items": []
        })
        assert response.status_code in [400, 422]

class TestListOrders:
    def test_list_orders_returns_list(self, client):
        response = client.get("/api/orders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_orders_empty_initially(self, client):
        orders = client.get("/api/orders").json()
        assert orders == []

    def test_list_orders_after_create(self, client, sample_order):
        client.post("/api/orders", json=sample_order)
        orders = client.get("/api/orders").json()
        assert len(orders) == 1

class TestGetOrder:
    def test_get_order_by_id(self, client, created_order):
        order_id = created_order["id"]
        response = client.get(f"/api/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["id"] == order_id

    def test_get_order_not_found(self, client):
        response = client.get("/api/orders/nonexistent-id-999")
        assert response.status_code == 404

class TestUpdateOrderStatus:
    def test_update_status_success(self, client, created_order):
        order_id = created_order["id"]
        response = client.patch(f"/api/orders/{order_id}/status?status=confirmed")
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    def test_update_all_valid_statuses(self, client, created_order):
        order_id = created_order["id"]
        for status in ["confirmed", "shipped", "delivered", "cancelled"]:
            response = client.patch(f"/api/orders/{order_id}/status?status={status}")
            assert response.status_code == 200

    def test_update_status_invalid(self, client, created_order):
        order_id = created_order["id"]
        response = client.patch(f"/api/orders/{order_id}/status?status=invalid")
        assert response.status_code == 400

    def test_update_status_not_found(self, client):
        response = client.patch("/api/orders/nonexistent/status?status=confirmed")
        assert response.status_code == 404
