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
class TestGetAllMissionsForCat:
    async def test_get_all_missions_for_cat_success(
        self,
        client: AsyncClient,
        cat_mission_target_factory
    ):
        test_data = await cat_mission_target_factory()

        response = await client.get(
            "/api/cats/missions",
            headers=test_data["headers"]
        )

        assert response.status_code == 200

    async def test_get_all_missions_for_cat_mission_not_found(
        self,
        client: AsyncClient,
        auth_headers
    ):
        response = await client.get(
            "/api/cats/missions",
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_get_all_missions_for_cat_without_auth(
        self,
        client: AsyncClient,
    ):
        response = await client.get(
            "/api/cats/missions",
        )

        assert response.status_code == 401

@pytest.mark.asyncio
class TestAssignCatToTarget:
    
    async def test_assign_cat_to_target_success(
        self,
        client: AsyncClient,
        cat_mission_target_factory,
    ):
        """Test successful assignment of authenticated cat to a target"""
        setup = await cat_mission_target_factory()
        target_uuid = setup['db_data']['target_uuid']

        response = await client.put(
            f"/api/cats/target/{target_uuid}/assign",
            headers=setup["headers"]
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
        cat_factory,
        auth_headers_factory,
        mission_db_factory,
        target_db_factory,
        db_session
    ):
        """Test that multiple different cats can be assigned to the same target"""
        cat1, password1 = await cat_factory(name="TestCat1")
        cat2, password2 = await cat_factory(name="TestCat2")
        mission = await mission_db_factory(cat_uuids=[cat1.uuid, cat2.uuid])
        target = await target_db_factory(mission)

        # Assign first cat
        headers1 = await auth_headers_factory(cat1.name, password1)
        response1 = await client.put(
            f"/api/cats/target/{target.uuid}/assign",
            headers=headers1
        )
        assert response1.status_code == 200
        
        # Assign second cat to same target
        headers2 = await auth_headers_factory(cat2.name, password2)
        response2 = await client.put(
            f"/api/cats/target/{target.uuid}/assign",
            headers=headers2
        )
        assert response2.status_code == 200
          
    async def test_assign_cat_to_multiple_targets(
        self,
        client: AsyncClient,
        cat_factory,
        auth_headers_factory,
        mission_db_factory,
        target_db_factory
    ):
        """Test that one cat can be assigned to multiple different targets"""
        cat, password = await cat_factory()
        mission = await mission_db_factory(cat_uuids=[cat.uuid])
        
        # Create two targets
        target1 = await target_db_factory(mission=mission, name="Target Alpha")
        target2 = await target_db_factory(mission=mission, name="Target Beta", country="USA")
        
        auth_headers = await auth_headers_factory(cat.name, password)
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
        cat_factory,
        auth_headers_factory,
        mission_db_factory,
        target_db_factory
    ):
        """Test assigning a cat to a target with COMPLETED status"""
        cat, password = await cat_factory()
        mission = await mission_db_factory(cat_uuids=[cat.uuid])

        target = await target_db_factory(mission=mission, status="completed")
        auth_headers = await auth_headers_factory(cat.name, password)
        
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


@pytest.mark.asyncio
class TestGetTurgetByUuid:
    async def test_get_target_by_uuid_success(
        self,
        client: AsyncClient,
        cat_mission_target_factory
    ):
        setup = await cat_mission_target_factory(assign_to_target=True)

        response = await client.get(
            f"/api/cats/target/{setup['target'].uuid}",
            headers=setup["headers"]
        )

        assert response.status_code == 200



