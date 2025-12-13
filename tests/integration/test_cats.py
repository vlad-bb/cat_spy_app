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
        client: AsyncClient
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
        test_data = await cat_mission_target_factory(assign_to_target=True)

        response = await client.get(
            f"/api/cats/target/{test_data['target'].uuid}",
            headers=test_data["headers"]
        )

        assert response.status_code == 200

    async def test_get_target_by_uuid_does_not_belong(
        self,
        client: AsyncClient,
        target_db_factory,
        auth_headers
    ):
        target = await target_db_factory()

        response = await client.get(
            f"/api/cats/target/{target.uuid}",
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Target does not belong to this cat"

    async def test_get_target_by_uuid_does_not_exist(
        self,
        client: AsyncClient,
        auth_headers
    ):
        target_uuid = str(uuid4())

        response = await client.get(
            f"/api/cats/target/{target_uuid}",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Target not found"

    async def test_get_target_by_uuid_without_auth(
        self,
        client: AsyncClient,
        target_db_factory
    ):
        target = await target_db_factory()

        response = await client.get(
            f"/api/cats/target/{target.uuid}",
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetMyTurgets:
    async def test_get_my_targets_success(
        self,
        client: AsyncClient,
        cat_mission_target_factory,
        target_db_factory
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True)
        mission = test_data["mission"]
        cat = test_data["cat"]
        await target_db_factory(mission=mission, assign_to_target=True, cat=cat)
        
        response = await client.get(
            "/api/cats/targets",
            headers=test_data["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_get_my_targets_not_found(
        self,
        client: AsyncClient,
        auth_headers
    ):
        response = await client.get(
            "/api/cats/targets",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "No targets found for this cat"

    async def test_get_my_targets_without_auth(
        self,
        client: AsyncClient,
        cat_mission_target_factory,
    ):
        await cat_mission_target_factory(assign_to_target=True)
        
        response = await client.get(
            "/api/cats/targets",
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestCompleteTurget:
    async def test_complete_target_success(
        self,
        client: AsyncClient,
        cat_mission_target_factory
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True)
        
        response = await client.put(
            f"/api/cats/target/complete/{test_data['db_data']['target_uuid']}",
            headers=test_data["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    async def test_complete_target_not_found(
        self,
        client: AsyncClient,
        auth_headers
    ):
        target_uuid = str(uuid4())
        response = await client.put(
            f"/api/cats/target/complete/{target_uuid}",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Target not found"

    async def test_complete_target_without_auth(
        self,
        client: AsyncClient,
        cat_mission_target_factory,
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True)
        
        response = await client.put(
            f"/api/cats/target/complete/{test_data['db_data']['target_uuid']}",
        )

        assert response.status_code == 401

@pytest.mark.asyncio
class TestCreateNoteForTarget:
    async def test_create_note_for_target_success(
        self, 
        client: AsyncClient, 
        cat_mission_target_factory,
        test_note
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True)
        target = test_data["target"]
        headers = test_data["headers"]
        
        # Act: create note
        response = await client.post(
            f"/api/cats/target-note/{target.uuid}",
            json={"content": test_note["content"]},
            headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        
        assert data["content"] == test_note["content"]
        assert data["target_uuid"] == str(target.uuid)

    async def test_create_note_target_not_found(
        self,
        client: AsyncClient,
        auth_headers,
        test_note
    ):
        target_uuid = str(uuid4())

        response = await client.post(
            f"/api/cats/target-note/{target_uuid}",
            json={"content": test_note["content"]},
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Target not found"

    async def test_create_note_for_target_cat_forbidden(
        self,
        client: AsyncClient,
        auth_headers,
        test_note,
        cat_mission_target_factory
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True)
        target = test_data["target"]

        response = await client.post(
            f"/api/cats/target-note/{target.uuid}",
            json={"content": test_note["content"]},
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Cat is not assigned to the mission of this target"

    async def test_create_note_for_target_without_auth(
        self,
        client: AsyncClient,
        cat_mission_target_factory,
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True)
        target = test_data["target"]
        
        response = await client.post(
            f"/api/cats/target-note/{target.uuid}",
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestGetNotes:
    async def test_get_notes_success(
        self, 
        client: AsyncClient, 
        cat_mission_target_factory
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True, create_note=True)
        headers = test_data["headers"]
        
        response = await client.get(
            "/api/cats/notes",
            headers=headers
        )

        assert response.status_code == 200

    async def test_get_notes_not_found(
            self,
            client: AsyncClient,
            auth_headers
    ):
        response = await client.get(
            "/api/cats/notes",
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "No notes found for this cat"

    async def test_get_notes_without_auth(
            self,
            client: AsyncClient
    ):
        response = await client.get(
            "/api/cats/notes"
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateNote:
    async def test_update_note_success(
        self, 
        client: AsyncClient, 
        cat_mission_target_factory
    ):
        test_data = await cat_mission_target_factory(assign_to_target=True, create_note=True)
        note = test_data["note"]
        headers = test_data["headers"]
        new_content = "Note after update"
        
        response = await client.put(
            f"/api/cats/note/{note.uuid}",
            json={"content": new_content},
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == new_content

    async def test_update_note_not_found(
        self, 
        client: AsyncClient,
        auth_headers
    ):
        note_uuid = str(uuid4())
        new_content = "Note after update"
        
        response = await client.put(
            f"/api/cats/note/{note_uuid}",
            json={"content": new_content},
            headers=auth_headers
        )

        assert response.status_code == 404

    async def test_update_note_completed_terget(
        self, 
        client: AsyncClient, 
        cat_mission_target_factory
    ):
        test_data = await cat_mission_target_factory(
            assign_to_target=True, 
            create_note=True, 
            target_kwargs={"status": "completed"}
            )
        note = test_data["note"]
        headers = test_data["headers"]
        new_content = "Note after update"
        
        response = await client.put(
            f"/api/cats/note/{note.uuid}",
            json={"content": new_content},
            headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Cannot update note for a completed target"

    async def test_update_note_cat_forbidden(
        self, 
        client: AsyncClient, 
        cat_mission_target_factory,
        auth_headers
    ):
        test_data = await cat_mission_target_factory(
            assign_to_target=True, 
            create_note=True
            )
        note = test_data["note"]
        new_content = "Note after update"
        
        response = await client.put(
            f"/api/cats/note/{note.uuid}",
            json={"content": new_content},
            headers=auth_headers
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"] == "Cat is not the author of this note"

    async def test_update_note_without_auth(
        self, 
        client: AsyncClient, 
        cat_mission_target_factory
    ):
        test_data = await cat_mission_target_factory(
            assign_to_target=True, 
            create_note=True
            )
        note = test_data["note"]
        new_content = "Note after update"
        
        response = await client.put(
            f"/api/cats/note/{note.uuid}",
            json={"content": new_content},
        )

        assert response.status_code == 401