def test_merchant_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "demo@settl.ai", "password": "settl123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["merchant_name"] == "Acme Retail India"


def test_merchant_login_failure(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "demo@settl.ai", "password": "wrong_password"}
    )
    assert response.status_code == 401


def test_get_current_merchant_me(client):
    # Login first
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "demo@settl.ai", "password": "settl123"}
    )
    token = login_resp.json()["access_token"]
    
    # Request profile
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "demo@settl.ai"
    assert data["name"] == "Acme Retail India"
