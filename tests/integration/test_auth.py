import pytest


@pytest.mark.asyncio
async def test_signup_success(client):
    """Note: async def and await!"""
    response = await client.post("/api/auth/signup", json={
        "name": "NewCat",
        "years_of_experience": 5,
        "password": "SecurePass123",
        "breed": "Siamese"
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_signup_duplicate_name(client, test_cat):
    response = await client.post("/api/auth/signup", json={
        "name": "TestCat",  # Already exists
        "password": "Pass123",
        "years_of_experience": 5,
        "breed": "Persian"
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client, test_cat):
    response = await client.post("/api/auth/login", data={
        "username": "TestCat",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_cat):
    response = await client.post("/api/auth/login", data={
        "username": "TestCat",
        "password": "WrongPass"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    response = await client.get("/api/cats/me", headers=auth_headers)
    print("Response type:", type(response))
    print("Response:", response)
    print("Response attributes:", dir(response))
    assert response.status_code == 200
    assert response.json()["name"] == "TestCat"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    response = await client.get("/api/cats/me")
    assert response.status_code == 401