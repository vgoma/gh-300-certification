"""Tests for the Mergington High School API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestRootEndpoint:
    """Tests for the GET / root endpoint."""
    
    def test_root_redirect(self, client: TestClient):
        """Test that root endpoint redirects to /static/index.html.
        
        Arrange: Set up TestClient
        Act: Make GET request to /
        Assert: Verify 307 redirect to /static/index.html
        """
        # Arrange
        # (TestClient is already set up via fixture)
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""
    
    def test_get_all_activities_success(self, client: TestClient):
        """Test that all activities are returned successfully.
        
        Arrange: Set up TestClient
        Act: Make GET request to /activities
        Assert: Verify response contains all 9 activities with correct structure
        """
        # Arrange
        expected_activity_count = 9
        expected_activity_names = {
            "Chess Club", "Programming Class", "Gym Class", "Basketball Team",
            "Soccer Club", "Art Studio", "Drama Club", "Debate Team", "Science Club"
        }
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activity_count
        assert set(data.keys()) == expected_activity_names
    
    def test_activities_response_structure(self, client: TestClient):
        """Test that each activity has the required fields.
        
        Arrange: Set up TestClient
        Act: Make GET request to /activities
        Assert: Verify each activity has description, schedule, max_participants, and participants fields
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data, dict)
            assert required_fields.issubset(set(activity_data.keys()))
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
    
    def test_activities_initial_participants(self, client: TestClient):
        """Test that activities have correct initial participant lists.
        
        Arrange: Set up TestClient
        Act: Make GET request to /activities
        Assert: Verify Chess Club has michael@mergington.edu and daniel@mergington.edu
        """
        # Arrange
        expected_chess_participants = {"michael@mergington.edu", "daniel@mergington.edu"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert set(data["Chess Club"]["participants"]) == expected_chess_participants


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client: TestClient):
        """Test successful signup for an activity.
        
        Arrange: Set up TestClient with an unregistered email
        Act: Make POST request to signup endpoint
        Assert: Verify student is added and response message is correct
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        
        # Verify student was added to participants
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants
    
    def test_signup_duplicate_email(self, client: TestClient):
        """Test that duplicate signup is rejected.
        
        Arrange: Set up TestClient with an already registered email
        Act: Make POST request to signup endpoint with existing participant
        Assert: Verify 400 error is returned with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert response.json() == {"detail": "Student already signed up for this activity"}
    
    def test_signup_invalid_activity(self, client: TestClient):
        """Test that signup for nonexistent activity returns 404.
        
        Arrange: Set up TestClient with invalid activity name
        Act: Make POST request to signup endpoint with nonexistent activity
        Assert: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Activity not found"}
    
    def test_signup_multiple_students(self, client: TestClient):
        """Test that multiple students can signup for the same activity.
        
        Arrange: Set up TestClient with two different emails
        Act: Make two POST requests to signup two different students
        Assert: Verify both students are in the participants list
        """
        # Arrange
        activity_name = "Art Studio"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        # Act
        response1 = client.post(f"/activities/{activity_name}/signup", params={"email": email1})
        response2 = client.post(f"/activities/{activity_name}/signup", params={"email": email2})
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/signup endpoint."""
    
    def test_unregister_success(self, client: TestClient):
        """Test successful unregistration from an activity.
        
        Arrange: Set up TestClient with a registered email
        Act: Make DELETE request to unregister endpoint
        Assert: Verify student is removed and response message is correct
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
        
        # Verify student was removed from participants
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email not in participants
    
    def test_unregister_not_signed_up(self, client: TestClient):
        """Test that unregistering a non-registered student returns 400.
        
        Arrange: Set up TestClient with an email not registered for activity
        Act: Make DELETE request to unregister endpoint with non-registered email
        Assert: Verify 400 error is returned
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"  # Not signed up
        
        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 400
        assert response.json() == {"detail": "Student not signed up for this activity"}
    
    def test_unregister_invalid_activity(self, client: TestClient):
        """Test that unregistration from nonexistent activity returns 404.
        
        Arrange: Set up TestClient with invalid activity name
        Act: Make DELETE request to unregister endpoint with nonexistent activity
        Assert: Verify 404 error is returned
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        
        # Assert
        assert response.status_code == 404
        assert response.json() == {"detail": "Activity not found"}
    
    def test_signup_then_unregister(self, client: TestClient):
        """Test the full flow of signing up and then unregistering.
        
        Arrange: Set up TestClient with a new email
        Act: Signup, then unregister the student
        Assert: Verify student is added then removed correctly
        """
        # Arrange
        activity_name = "Programming Class"
        email = "fullflow@mergington.edu"
        
        # Act: Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup", params={"email": email})
        assert signup_response.status_code == 200
        
        # Verify student was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity_name]["participants"]
        
        # Act: Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})
        assert unregister_response.status_code == 200
        
        # Assert: Verify student was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity_name]["participants"]
