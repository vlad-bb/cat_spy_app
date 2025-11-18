import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
class TestCreateMission:
    """Test suite for mission creation endpoint"""
    async def test_create_mission_success(
        self,
        client,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()
        response = await client.post(
            "/api/admin/mission/create",
            json=mission_data,
            headers=admin_headers
        )
        print(type(response))
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "uuid" in data
        assert data["name"] == mission_data["name"]
        assert data["description"] == mission_data["description"]
        assert data["status"] == "pending"
        assert "created_at" in data
        assert len(data["targets"]) == 1
        assert data["targets"][0]["name"] == "The Red Dot Mastermind"
        assert data["targets"][0]["country"] == "Japan"
        assert data["cat_uuids"] == []
    
    async def test_create_mission_with_multiple_targets(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory,
    ):
        targets = [
            {
                "name": "Primary Target",
                "country": "Japan"
            },
            {
                "name": "Secondary Target",
                "country": "Japan"
            },
            {
                "name": "Tertiary Target",
                "country": "Japan"
            }
        ]
        mission_data = mission_data_factory(targets=targets)

        """Test creating mission with 3 targets (maximum allowed)"""
        response = await client.post(
            "/api/admin/mission/create",
            json=mission_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert len(data["targets"]) == 3
        assert data["targets"][0]["name"] == "Primary Target"
        assert data["targets"][1]["name"] == "Secondary Target"
        assert data["targets"][2]["name"] == "Tertiary Target"
    
    async def test_create_mission_with_assigned_cats(
        self,
        client: AsyncClient,
        admin_headers,
        test_cat,
        mission_data_factory
    ):
        mission_data = mission_data_factory(cat_uuids=[str(test_cat.uuid)])

        """Test creating mission with assigned cats"""
        response = await client.post(
            "/api/admin/mission/create",
            json=mission_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert len(data["cat_uuids"]) == 1
        assert data["cat_uuids"][0] == mission_data["cat_uuids"][0]
    
    async def test_create_mission_unauthorized(
        self,
        client: AsyncClient,
        auth_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test that non-admin users cannot create missions"""
        response = await client.post(
            "/api/admin/mission/create",
            json=mission_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_create_mission_without_auth(
        self,
        client: AsyncClient,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test that unauthenticated requests are rejected"""
        response = await client.post(
            "/api/admin/mission/create",
            json=mission_data
        )
        
        assert response.status_code == 401
    
    async def test_create_mission_empty_name(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test validation fails with empty name"""
        invalid_data = mission_data.copy()
        invalid_data["name"] = ""
        
        response = await client.post(
            "/api/admin/mission/create",
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422
    
    async def test_create_mission_name_too_long(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test validation fails with name exceeding 100 characters"""
        invalid_data = mission_data.copy()
        invalid_data["name"] = "A" * 101
        
        response = await client.post(
            "/api/admin/mission/create",
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422
    
    async def test_create_mission_description_too_long(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test validation fails with description exceeding 255 characters"""
        invalid_data = mission_data.copy()
        invalid_data["description"] = "A" * 256
        
        response = await client.post(
            "/api/admin/mission/create",
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422
    
    async def test_create_mission_no_targets(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test validation fails with no targets"""
        invalid_data = mission_data.copy()
        invalid_data["targets"] = []
        
        response = await client.post(
            "/api/admin/mission/create",
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422
    
    async def test_create_mission_too_many_targets(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test validation fails with more than 3 targets"""
        invalid_data = mission_data.copy()
        invalid_data["targets"] = [
            {"name": f"Target {i}", "country": "Poland"}
            for i in range(4)
        ]
        
        response = await client.post(
            "/api/admin/mission/create",
            json=invalid_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422
    
    async def test_create_mission_whitespace_stripping(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test that whitespace is stripped from name and description"""
        data_with_whitespace = mission_data.copy()
        data_with_whitespace["name"] = "  Mission Name  "
        data_with_whitespace["description"] = "  Mission Description  "
        
        response = await client.post(
            "/api/admin/mission/create",
            json=data_with_whitespace,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Mission Name"
        assert data["description"] == "Mission Description"
    
    async def test_create_mission_with_nonexistent_cat(
        self,
        client: AsyncClient,
        admin_headers,
        mission_data_factory
    ):
        mission_data = mission_data_factory()

        """Test creating mission with non-existent cat UUID"""
        invalid_data = mission_data.copy()
        invalid_data["cat_uuids"] = [str(uuid4())]
        
        response = await client.post(
            "/api/admin/mission/create",
            json=invalid_data,
            headers=admin_headers
        )
        
        # Depending on your implementation, this might be 404 or 422
        assert response.status_code in [404, 422]
    
