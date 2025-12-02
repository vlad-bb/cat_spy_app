import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
class TestGetMyCat:
    async def test_get_my_cat_success(
        self,
        client: AsyncClient,
        auth_headers
    ):
        response = await client.get(
            "/api/cats/me", 
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["name"] == "TestCat"
    
    async def test_get_my_cat_by_uuid_without_auth(
        self,
        client: AsyncClient,
        test_cat
    ):
        response = await client.get(
            "/api/cats/me",
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAssignCatToTarget:
    
    async def test_assign_cat_to_target_success(
        self,
        client: AsyncClient,
        auth_headers,
        target_db_factory
    ):
        """Test successful assignment of authenticated cat to a target"""
        target = await target_db_factory()

        response = await client.put(
            f"/api/cats/target/{target.uuid}/assign",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
    
    async def test_assign_cat_to_nonexistent_target(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test assignment to a target that doesn't exist"""
        nonexistent_target_uuid = uuid4()
        
        response = await client.put(
            f"/api/targets/{nonexistent_target_uuid}/assign",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        
    async def test_assign_multiple_cats_to_same_target(
        self,
        client: AsyncClient,
        auth_headers_factory,
        multiple_test_cats,
        target_db_factory
    ):
        """Test that multiple different cats can be assigned to the same target"""
        target = await target_db_factory()
        
        # Assign first cat
        headers1 = await auth_headers_factory("TestCat1", "TestPass123!")
        response1 = await client.put(
            f"/api/cats/target/{target.uuid}/assign",
            headers=headers1
        )
        assert response1.status_code == 200
        
        # Assign second cat to same target
        headers2 = await auth_headers_factory("TestCat2", "TestPass123!")
        response2 = await client.put(
            f"/api/cats/target/{target.uuid}/assign",
            headers=headers2
        )
        assert response2.status_code == 200
          
    async def test_assign_cat_to_multiple_targets(
        self,
        client: AsyncClient,
        auth_headers,
        target_db_factory
    ):
        """Test that one cat can be assigned to multiple different targets"""
        # Create two targets
        target1 = await target_db_factory(name="Target Alpha")
        target2 = await target_db_factory(name="Target Beta", country="USA")
        
        # Assign same cat to first target
        response1 = await client.put(
            f"/api/cats/target/{target1.uuid}/assign",
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # Assign same cat to second target
        response2 = await client.put(
            f"/api/cats/target/{target2.uuid}/assign",
            headers=auth_headers
        )
        assert response2.status_code == 200
        
    async def test_assign_cat_to_completed_target(
        self,
        client: AsyncClient,
        auth_headers,
        target_db_factory
    ):
        """Test assigning a cat to a target with COMPLETED status"""
        target = await target_db_factory(status="completed")
        
        response = await client.put(
            f"/api/cats/target/{target.uuid}/assign",
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    async def test_get_my_cat_by_uuid_without_auth(
        self,
        client: AsyncClient,
        target_db_factory
    ):
        target = await target_db_factory()

        response = await client.put(
            f"/api/cats/target/{target.uuid}/assign",
        )
        
        assert response.status_code == 401