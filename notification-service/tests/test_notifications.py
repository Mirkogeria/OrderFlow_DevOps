# test_notification.py — Unit tests for notification-service
# Run with: python -m pytest tests/ -v --cov=. --cov-report=term
# Part of OrderFlow CI/CD pipeline

import pytest
from fastapi.testclient import TestClient


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def client():
    import main
    main.notifications_db.clear()
    main.notification_counter = 0
    return TestClient(main.app)

@pytest.fixture
def sample_notification():
    return {
        "order_id": 1,
        "customer_name": "Mario Rossi",
        "event_type": "order.created"
    }

@pytest.fixture
def created_notification(client, sample_notification):
    response = client.post("/api/notifications", json=sample_notification)
    assert response.status_code == 201
    return response.json()


# ========================================
# Health Check Tests
# ========================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_returns_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "notification-service"

    def test_health_includes_version(self, client):
        assert "version" in client.get("/health").json()


# ========================================
# Create Notification Tests
# ========================================

class TestCreateNotification:
    def test_create_returns_201(self, client, sample_notification):
        assert client.post("/api/notifications", json=sample_notification).status_code == 201

    def test_create_returns_correct_data(self, client, sample_notification):
        data = client.post("/api/notifications", json=sample_notification).json()
        assert data["order_id"] == 1
        assert data["customer_name"] == "Mario Rossi"
        assert data["event_type"] == "order.created"
        assert data["status"] == "sent"
        assert "id" in data
        assert "message" in data

    def test_create_generates_message_with_order_id(self, client):
        payload = {"order_id": 42, "customer_name": "Luigi Verdi", "event_type": "order.shipped"}
        data = client.post("/api/notifications", json=payload).json()
        assert "42" in data["message"]

    def test_create_all_event_types(self, client):
        events = ["order.created", "order.confirmed", "order.shipped", "order.delivered", "order.cancelled"]
        for event in events:
            payload = {"order_id": 1, "customer_name": "Test", "event_type": event}
            response = client.post("/api/notifications", json=payload)
            assert response.status_code == 201
            assert response.json()["event_type"] == event

    def test_create_unknown_event_type(self, client):
        payload = {"order_id": 1, "customer_name": "Test", "event_type": "order.unknown"}
        data = client.post("/api/notifications", json=payload).json()
        assert data["status"] == "sent"  # accettato comunque
        assert "order.unknown" in data["message"]

    def test_create_increments_id(self, client, sample_notification):
        first = client.post("/api/notifications", json=sample_notification).json()
        second = client.post("/api/notifications", json=sample_notification).json()
        assert second["id"] == first["id"] + 1

    def test_create_includes_created_at(self, client, sample_notification):
        data = client.post("/api/notifications", json=sample_notification).json()
        assert "created_at" in data

    def test_create_missing_fields(self, client):
        assert client.post("/api/notifications", json={}).status_code == 422


# ========================================
# List Notifications Tests
# ========================================

class TestListNotifications:
    def test_list_returns_200(self, client):
        assert client.get("/api/notifications").status_code == 200

    def test_list_empty_initially(self, client):
        data = client.get("/api/notifications").json()
        assert data["notifications"] == []
        assert data["total"] == 0

    def test_list_structure(self, client):
        data = client.get("/api/notifications").json()
        assert "notifications" in data
        assert "total" in data
        assert isinstance(data["notifications"], list)

    def test_list_after_create(self, client, sample_notification):
        client.post("/api/notifications", json=sample_notification)
        data = client.get("/api/notifications").json()
        assert data["total"] == 1

    def test_filter_by_order_id(self, client, sample_notification):
        client.post("/api/notifications", json=sample_notification)
        # Notifica per ordine diverso
        client.post("/api/notifications", json={
            "order_id": 999, "customer_name": "Altri", "event_type": "order.created"
        })
        data = client.get("/api/notifications", params={"order_id": 1}).json()
        assert data["total"] == 1
        assert data["notifications"][0]["order_id"] == 1

    def test_filter_order_id_no_results(self, client):
        data = client.get("/api/notifications", params={"order_id": 99999}).json()
        assert data["total"] == 0
        assert data["notifications"] == []


# ========================================
# Get Notification Tests
# ========================================

class TestGetNotification:
    def test_get_by_id(self, client, created_notification):
        nid = created_notification["id"]
        response = client.get(f"/api/notifications/{nid}")
        assert response.status_code == 200
        assert response.json()["id"] == nid

    def test_get_correct_data(self, client, created_notification):
        nid = created_notification["id"]
        data = client.get(f"/api/notifications/{nid}").json()
        assert data["order_id"] == 1
        assert data["customer_name"] == "Mario Rossi"

    def test_get_not_found(self, client):
        assert client.get("/api/notifications/99999").status_code == 404
