import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
class TestGetAllCats:
    """Test suite for extracting all cats"""
    async def test_get_all_cats_success(
        self,
        client: AsyncClient,
        admin_headers,
        multiple_test_cats
    ):
        response = await client.get(
            "/api/admin/cats",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data[0]["name"] == "AdminCat"
        assert data[1]["name"] == "TestCat1"
        assert data[2]["breed"] == "Siamese"
        assert data[3]["years_of_experience"] == 5
        assert len(data) == 4

    async def test_get_all_cats_unauthorized(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test that non-admin users cannot extract all cats"""
        response = await client.get(
            "/api/admin/cats",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_get_all_cats_without_auth(
        self,
        client: AsyncClient,
    ):
        """Test that unauthenticated requests are rejected"""
        response = await client.get(
            "/api/admin/cats",
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetCatByName:
    """Test suite for extracting cat by its name"""
    async def test_get_cat_by_name_success(
        self,
        client: AsyncClient,
        admin_headers,
        multiple_test_cats
    ):
        responce = await client.get(
            "/api/admin/cats/name",
            params={"search_query": "TestCat3"},
            headers=admin_headers
        )
        assert responce.status_code == 200
        data = responce.json()

        assert data[0]["breed"] == "Maine Coon"

    async def test_get_cat_by_name_partial_name(
        self, 
        client: AsyncClient,
        admin_headers,
        multiple_test_cats
    ):
        responce = await client.get(
            "/api/admin/cats/name",
            params={"search_query": "est"},
            headers=admin_headers
        )
        assert responce.status_code == 200
        data = responce.json()

        assert len(data) == 3
        assert data[0]["name"] == "TestCat1"

    async def test_get_cat_by_name_not_found(
        self,
        client: AsyncClient,
        admin_headers
    ):
        response = await client.get(
            "/api/admin/cats/name",
            params={"search_query": "NonExistentCat"},
            headers=admin_headers
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Cat not found"

    async def test_get_cat_by_name_unauthorized(
        self,
        client: AsyncClient,
        auth_headers,
        multiple_test_cats
    ):
        """Test that non-admin users cannot perform search"""
        response = await client.get(
            "/api/admin/cats/name",
            params={"search_query": "TestCat3"},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_get_cat_by_name_without_auth(
        self,
        client: AsyncClient,
        multiple_test_cats
    ):
        """Test that unauthenticated requests are rejected"""
        response = await client.get(
            "/api/admin/cats/name",
            params={"search_query": "TestCat3"},
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateCatSalary:
    """Test suite for updating cat's salary"""
    async def test_update_cat_salary_success(
        self,
        client: AsyncClient,
        admin_headers,
        test_cat
    ):
        cat_uuid = test_cat.uuid
        responce = await client.put(
            f"/api/admin/cats/update/{cat_uuid}",
            params={"salary": 10000},
            headers=admin_headers
        )
        assert responce.status_code == 200
        data = responce.json()

        assert data["salary"] == 10000

    async def test_update_cat_salary_negative_value(
        self,
        client: AsyncClient,
        admin_headers,
        test_cat
    ):
        """Test with negative salary (validation error)"""
        cat_uuid = test_cat.uuid
        
        response = await client.put(
            f"/api/admin/cats/update/{cat_uuid}",
            params={"salary": -100},
            headers=admin_headers
        )
        
        assert response.status_code == 422

    async def test_update_cat_salary_missing_param(
        self,
        client: AsyncClient,
        admin_headers,
        test_cat
    ):
        """Test without salary parameter"""
        cat_uuid = test_cat.uuid
        
        response = await client.put(
            f"/api/admin/cats/update/{cat_uuid}",
            headers=admin_headers
            # No salary parameter
        )
        
        assert response.status_code == 422

    async def test_update_cat_salary_invalid_uuid(
        self,
        client: AsyncClient,
        admin_headers
    ):
        """Test with invalid UUID"""
        cat_uuid = uuid4()

        response = await client.put(
            f"/api/admin/cats/update/{cat_uuid}",
            params={"salary": 10000},
            headers=admin_headers
        )
        
        assert response.status_code == 404
        data = response.json()

        assert data["detail"] == "Cat not found"

    async def test_update_cat_salary_unauthorized(
        self,
        client: AsyncClient,
        auth_headers,
        test_cat
    ):
        """Test that non-admin users cannot update cat's salary"""
        cat_uuid = test_cat.uuid

        response = await client.put(
            f"/api/admin/cats/update/{cat_uuid}",
            params={"salary": 10000},
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_update_cat_salary_without_auth(
        self,
        client: AsyncClient,
        test_cat
    ):
        """Test that unauthenticated requests are rejected"""
        cat_uuid = test_cat.uuid

        response = await client.put(
            f"/api/admin/cats/update/{cat_uuid}",
            params={"salary": 10000},
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteCatByUuid:
    """Test suite for deleting cat by uuid"""
    async def test_delete_cat_by_uuid_success(
        self,
        client: AsyncClient,
        admin_headers,
        test_cat
    ):
        cat_uuid = test_cat.uuid
        response = await client.delete(
            f"/api/admin/cats/delete/{cat_uuid}",
            headers=admin_headers
        )

        assert response.status_code == 204

    async def test_delete_cat_by_uuid_not_found(
        self,
        client: AsyncClient,
        admin_headers
    ):
        cat_uuid = uuid4()
        response = await client.delete(
            f"/api/admin/cats/delete/{cat_uuid}",
            headers=admin_headers
        )

        assert response.status_code == 404

    async def test_delete_cat_by_uuid_unauthorized(
        self,
        client: AsyncClient,
        auth_headers,
        test_cat
    ):
        """Test that non-admin users cannot delete cat by uuid"""
        cat_uuid = test_cat.uuid

        response = await client.delete(
            f"/api/admin/cats/delete/{cat_uuid}",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_delete_cat_by_uuid_without_auth(
        self,
        client: AsyncClient,
        test_cat
    ):
        """Test that unauthenticated requests are rejected"""
        cat_uuid = test_cat.uuid

        response = await client.delete(
            f"/api/admin/cats/delete/{cat_uuid}",
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetCatByUuid:
    """Test suite for getting cat by uuid"""
    async def test_get_cat_by_uuid_success(
        self,
        client: AsyncClient,
        admin_headers,
        test_cat
    ):
        cat_uuid = test_cat.uuid
        response = await client.get(
            f"/api/admin/cats/{cat_uuid}",
            headers=admin_headers
        )

        assert response.status_code == 200

    async def test_get_cat_by_uuid_not_found(
        self,
        client: AsyncClient,
        admin_headers
    ):
        cat_uuid = uuid4()
        response = await client.get(
            f"/api/admin/cats/{cat_uuid}",
            headers=admin_headers
        )

        assert response.status_code == 404

    async def test_get_cat_by_uuid_unauthorized(
        self,
        client: AsyncClient,
        auth_headers,
        test_cat
    ):
        """Test that non-admin users cannot get cat by uuid"""
        cat_uuid = test_cat.uuid

        response = await client.get(
            f"/api/admin/cats/{cat_uuid}",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_get_cat_by_uuid_without_auth(
        self,
        client: AsyncClient,
        test_cat
    ):
        """Test that unauthenticated requests are rejected"""
        cat_uuid = test_cat.uuid

        response = await client.get(
            f"/api/admin/cats/{cat_uuid}",
        )
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestCreateMission:
    """Test suite for mission creation endpoint"""
    async def test_create_mission_success(
        self,
        client: AsyncClient,
        admin_headers,
        mission_factory
    ):
        mission_data = mission_factory()
        response = await client.post(
            "/api/admin/mission/create",
            json=mission_data,
            headers=admin_headers
        )
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
        mission_factory,
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
        mission_data = mission_factory(targets=targets)

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
        mission_factory
    ):
        mission_data = mission_factory(cat_uuids=[str(test_cat.uuid)])

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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
        mission_factory
    ):
        mission_data = mission_factory()

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


@pytest.mark.asyncio
class TestGetAllMissions:
    async def test_get_all_missions(
        self,
        client: AsyncClient,
        admin_headers,
        mission_db_factory
    ):
        # Create missions in the database
        await mission_db_factory()
        await mission_db_factory()
        await mission_db_factory()
        
        response = await client.get(
            "/api/admin/missions",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3

    async def test_get_all_missions_empty_result(
        self,
        client: AsyncClient,
        admin_headers
    ):
        responce = await client.get(
            "/api/admin/missions",
            headers=admin_headers
        )

        assert responce.status_code == 200
        data = responce.json()

        assert len(data) == 0

    async def test_get_all_missions_unauthorized(
        self,
        client: AsyncClient,
        auth_headers,
        mission_db_factory
    ):
        """Test that non-admin users cannot get all missions"""
        # Create missions in the database
        await mission_db_factory()
        await mission_db_factory()
        await mission_db_factory()

        response = await client.get(
            "/api/admin/missions",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_get_all_missions_without_auth(
        self,
        client: AsyncClient,
        mission_db_factory
    ):
        """Test that unauthenticated requests are rejected"""
                # Create missions in the database
        await mission_db_factory()
        await mission_db_factory()
        await mission_db_factory()

        response = await client.get(
            "/api/admin/missions",
        )
        
        assert response.status_code == 401
    

@pytest.mark.asyncio
class TestGetMissionByUuid:
    async def test_get_mission_by_uuid_success(
        self,
        client: AsyncClient,
        admin_headers,
        mission_db_factory
    ):
        mission = await mission_db_factory()      
        mission_uuid = mission.uuid

        responce = await client.get(
            f"/api/admin/mission/{mission_uuid}",
            headers=admin_headers
        )

        assert responce.status_code == 200
        data = responce.json()

        assert data["uuid"] == str(mission_uuid)

    async def test_get_mission_by_uuid_not_found(
        self,
        client: AsyncClient,
        admin_headers
    ):
        mission_uuid = str(uuid4())

        responce = await client.get(
            f"/api/admin/mission/{mission_uuid}",
            headers=admin_headers
        )

        assert responce.status_code == 404
        data = responce.json()

        assert data["detail"] == "Mission not found"

    async def test_get_mission_by_uuid_unauthorized(
        self,
        client: AsyncClient,
        auth_headers,
        mission_db_factory
    ):
        """Test that non-admin users cannot get mission by uuid"""
        # Create mission in the database
        mission = await mission_db_factory()
        mission_uuid = mission.uuid

        response = await client.get(
            f"/api/admin/mission/{mission_uuid}",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_get_mission_by_uuid_without_auth(
        self,
        client: AsyncClient,
        mission_db_factory
    ):
        """Test that unauthenticated requests are rejected"""
        # Create mission in the database
        mission = await mission_db_factory()
        mission_uuid = mission.uuid

        response = await client.get(
            f"/api/admin/mission/{mission_uuid}",
        )
        
        assert response.status_code == 401