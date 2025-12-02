import pytest


@pytest.mark.asyncio
class TestSignUp:
    "Test suite for sign up endpoint"

    async def test_signup_success(self, client):
        """Note: async def and await!"""
        response = await client.post("/api/auth/signup", json={
            "name": "NewCat",
            "years_of_experience": 5,
            "password": "SecurePass123",
            "breed": "Siamese"
        })
        assert response.status_code == 201


    @pytest.mark.asyncio
    async def test_signup_duplicate_name(self, client, test_cat):
        response = await client.post("/api/auth/signup", json={
            "name": "TestCat",  # Already exists
            "password": "Pass123",
            "years_of_experience": 5,
            "breed": "Persian"
        })
        assert response.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    "Test suite for login endpoint"
    
    async def test_login_success(self, client, test_cat):
        response = await client.post("/api/auth/login", data={
            "username": "TestCat",
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_cat):
        response = await client.post("/api/auth/login", data={
            "username": "TestCat",
            "password": "WrongPass"
        })
        assert response.status_code == 401


