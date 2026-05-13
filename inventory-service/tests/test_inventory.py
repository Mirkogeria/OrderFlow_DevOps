# test_inventory.py — Unit tests for inventory-service
# Run with: python -m pytest tests/ -v --cov=. --cov-report=term
# Part of OrderFlow CI/CD pipeline

import pytest
from fastapi.testclient import TestClient


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def client():
    from main import app
    return TestClient(app)


# ========================================
# Health Check Tests
# ========================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_returns_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "inventory-service"

    def test_health_includes_version(self, client):
        data = client.get("/health").json()
        assert "version" in data


# ========================================
# List Products Tests
# ========================================

class TestListProducts:
    def test_list_products_returns_200(self, client):
        assert client.get("/api/products").status_code == 200

    def test_list_products_returns_list(self, client):
        assert isinstance(client.get("/api/products").json(), list)

    def test_list_products_not_empty(self, client):
        products = client.get("/api/products").json()
        assert len(products) == 5  # sappiamo che il db ha 5 prodotti

    def test_products_have_required_fields(self, client):
        products = client.get("/api/products").json()
        for product in products:
            assert "id" in product
            assert "name" in product
            assert "price" in product
            assert "stock" in product
            assert "category" in product

    def test_products_prices_are_positive(self, client):
        products = client.get("/api/products").json()
        for product in products:
            assert product["price"] > 0

    def test_products_stock_is_non_negative(self, client):
        products = client.get("/api/products").json()
        for product in products:
            assert product["stock"] >= 0


# ========================================
# Get Product Tests
# ========================================

class TestGetProduct:
    def test_get_existing_product(self, client):
        response = client.get("/api/products/1")
        assert response.status_code == 200

    def test_get_product_correct_data(self, client):
        data = client.get("/api/products/1").json()
        assert data["id"] == 1
        assert data["name"] == "Laptop Pro 15"
        assert data["price"] == 1299.99
        assert data["category"] == "electronics"

    def test_get_product_2(self, client):
        data = client.get("/api/products/2").json()
        assert data["name"] == "Wireless Mouse"
        assert data["category"] == "accessories"

    def test_get_product_not_found(self, client):
        assert client.get("/api/products/99999").status_code == 404

    def test_get_product_zero_id(self, client):
        assert client.get("/api/products/0").status_code == 404


# ========================================
# Check Stock Tests
# ========================================

class TestCheckStock:
    def test_check_stock_returns_200(self, client):
        assert client.get("/api/products/1/check-stock").status_code == 200

    def test_check_stock_default_quantity(self, client):
        data = client.get("/api/products/1/check-stock").json()
        assert data["requested"] == 1
        assert data["available"] is True  # Laptop ha 50 pezzi

    def test_check_stock_available_true(self, client):
        # Laptop Pro 15 ha stock=50, chiediamo 10
        data = client.get("/api/products/1/check-stock", params={"quantity": 10}).json()
        assert data["available"] is True
        assert data["current_stock"] == 50
        assert data["requested"] == 10

    def test_check_stock_available_false(self, client):
        # Laptop Pro 15 ha stock=50, chiediamo 9999
        data = client.get("/api/products/1/check-stock", params={"quantity": 9999}).json()
        assert data["available"] is False

    def test_check_stock_exact_quantity(self, client):
        # Chiediamo esattamente lo stock disponibile → deve essere True
        stock = client.get("/api/products/1").json()["stock"]
        data = client.get("/api/products/1/check-stock", params={"quantity": stock}).json()
        assert data["available"] is True

    def test_check_stock_response_fields(self, client):
        data = client.get("/api/products/1/check-stock").json()
        assert "product_id" in data
        assert "product_name" in data
        assert "requested" in data
        assert "current_stock" in data
        assert "available" in data

    def test_check_stock_not_found(self, client):
        assert client.get("/api/products/99999/check-stock").status_code == 404

    def test_check_stock_product_name_matches(self, client):
        data = client.get("/api/products/1/check-stock").json()
        assert data["product_name"] == "Laptop Pro 15"
        assert data["product_id"] == 1
