import json
import logging

import pytest
from django.test import Client

logger = logging.getLogger("core")


@pytest.fixture
def client():
    return Client()


def _post(client, url, data):
    return client.post(url, json.dumps(data), content_type="application/json")


@pytest.mark.django_db
class TestFullFlow:
    """Test the complete flow: create student -> create course -> enroll -> add grades -> query."""

    def test_complete_flow(self, client):
        logger.info("=== Starting complete flow test ===")

        # Create student
        resp = _post(client, "/api/students/", {"name": "Alice"})
        assert resp.status_code == 201
        student = resp.json()
        assert student["name"] == "Alice"
        student_id = student["id"]

        # Create courses
        resp = _post(client, "/api/courses/", {"name": "Math"})
        assert resp.status_code == 201
        math = resp.json()
        math_id = math["id"]

        resp = _post(client, "/api/courses/", {"name": "Physics"})
        assert resp.status_code == 201
        physics = resp.json()
        physics_id = physics["id"]

        # Enroll in both courses
        resp = _post(
            client,
            "/api/enrollments/",
            {"student_id": student_id, "course_id": math_id},
        )
        assert resp.status_code == 201

        resp = _post(
            client,
            "/api/enrollments/",
            {"student_id": student_id, "course_id": physics_id},
        )
        assert resp.status_code == 201

        # Add grades
        resp = _post(
            client,
            "/api/grades/",
            {"student_id": student_id, "course_id": math_id, "value": 95},
        )
        assert resp.status_code == 201
        assert resp.json()["value"] == 95

        resp = _post(
            client,
            "/api/grades/",
            {"student_id": student_id, "course_id": math_id, "value": 85},
        )
        assert resp.status_code == 201

        resp = _post(
            client,
            "/api/grades/",
            {"student_id": student_id, "course_id": physics_id, "letter": "B"},
        )
        assert resp.status_code == 201

        # Query student courses
        resp = client.get(f"/api/students/{student_id}/courses/")
        assert resp.status_code == 200
        courses = resp.json()["courses"]
        assert len(courses) == 2
        course_names = {c["name"] for c in courses}
        assert course_names == {"Math", "Physics"}

        # Query course students
        resp = client.get(f"/api/courses/{math_id}/students/")
        assert resp.status_code == 200
        students = resp.json()["students"]
        assert len(students) == 1
        assert students[0]["name"] == "Alice"

        # Query grades
        resp = client.get(f"/api/students/{student_id}/courses/{math_id}/grades/")
        assert resp.status_code == 200
        assert resp.json()["grades"] == [95, 85]

        # Query report card
        resp = client.get(f"/api/students/{student_id}/report/")
        assert resp.status_code == 200
        report = resp.json()
        assert report["student"] == "Alice"
        assert len(report["report"]) == 2

        by_course = {r["course"]: r for r in report["report"]}
        assert by_course["Math"]["grades"] == [95, 85]
        assert by_course["Math"]["average"] == 90
        assert by_course["Math"]["letter"] == "A-"

        logger.info("=== Complete flow test passed ===")


@pytest.mark.django_db
class TestErrorCases:
    """Test error responses from the API."""

    def test_duplicate_enrollment_returns_409(self, client):
        resp = _post(client, "/api/students/", {"name": "Bob"})
        student_id = resp.json()["id"]

        resp = _post(client, "/api/courses/", {"name": "History"})
        course_id = resp.json()["id"]

        resp = _post(
            client,
            "/api/enrollments/",
            {"student_id": student_id, "course_id": course_id},
        )
        assert resp.status_code == 201

        # Duplicate enrollment
        resp = _post(
            client,
            "/api/enrollments/",
            {"student_id": student_id, "course_id": course_id},
        )
        assert resp.status_code == 409
        assert "already enrolled" in resp.json()["error"].lower()

    def test_grade_not_enrolled_returns_404(self, client):
        resp = _post(client, "/api/students/", {"name": "Charlie"})
        student_id = resp.json()["id"]

        resp = _post(client, "/api/courses/", {"name": "Art"})
        course_id = resp.json()["id"]

        # Try to add grade without enrollment
        resp = _post(
            client,
            "/api/grades/",
            {"student_id": student_id, "course_id": course_id, "value": 80},
        )
        assert resp.status_code == 404
        assert "not enrolled" in resp.json()["error"].lower()

    def test_invalid_grade_value_returns_400(self, client):
        resp = _post(client, "/api/students/", {"name": "Diana"})
        student_id = resp.json()["id"]

        resp = _post(client, "/api/courses/", {"name": "Music"})
        course_id = resp.json()["id"]

        _post(
            client,
            "/api/enrollments/",
            {"student_id": student_id, "course_id": course_id},
        )

        # Grade > 100
        resp = _post(
            client,
            "/api/grades/",
            {"student_id": student_id, "course_id": course_id, "value": 101},
        )
        assert resp.status_code == 400

    def test_invalid_letter_grade_returns_400(self, client):
        resp = _post(client, "/api/students/", {"name": "Eve"})
        student_id = resp.json()["id"]

        resp = _post(client, "/api/courses/", {"name": "PE"})
        course_id = resp.json()["id"]

        _post(
            client,
            "/api/enrollments/",
            {"student_id": student_id, "course_id": course_id},
        )

        resp = _post(
            client,
            "/api/grades/",
            {"student_id": student_id, "course_id": course_id, "letter": "Z"},
        )
        assert resp.status_code == 400

    def test_student_not_found_returns_404(self, client):
        resp = client.get("/api/students/9999/courses/")
        assert resp.status_code == 404

    def test_course_not_found_returns_404(self, client):
        resp = client.get("/api/courses/9999/students/")
        assert resp.status_code == 404

    def test_missing_name_returns_400(self, client):
        resp = _post(client, "/api/students/", {})
        assert resp.status_code == 400

        resp = _post(client, "/api/courses/", {})
        assert resp.status_code == 400

    def test_grades_not_enrolled_returns_404(self, client):
        resp = _post(client, "/api/students/", {"name": "Frank"})
        student_id = resp.json()["id"]

        resp = _post(client, "/api/courses/", {"name": "Biology"})
        course_id = resp.json()["id"]

        resp = client.get(f"/api/students/{student_id}/courses/{course_id}/grades/")
        assert resp.status_code == 404
