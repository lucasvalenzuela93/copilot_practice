import copy
import pytest

from httpx import AsyncClient, ASGITransport

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original))


@pytest.mark.asyncio
async def test_get_activities_returns_activity_dictionary():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/activities")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert expected_activity in body
    assert body[expected_activity]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"


@pytest.mark.asyncio
async def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "temporary_student@mergington.edu"
    assert email not in activities[activity_name]["participants"]
    before_count = len(activities[activity_name]["participants"])

    # Act
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert len(activities[activity_name]["participants"]) == before_count + 1
    assert email in activities[activity_name]["participants"]


@pytest.mark.asyncio
async def test_signup_for_activity_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    assert email in activities[activity_name]["participants"]

    # Act
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


@pytest.mark.asyncio
async def test_remove_participant_removes_existing_participant():
    # Arrange
    activity_name = "Programming Class"
    email = "temporary_student@mergington.edu"
    if email not in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].append(email)
    assert email in activities[activity_name]["participants"]

    # Act
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email},
        )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


@pytest.mark.asyncio
async def test_signup_invalid_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    # Act
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
