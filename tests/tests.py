import pytest

from core.exceptions import AlreadyEnrolledError, InvalidGradeError, NotEnrolledError
from core.grades import letter_to_value, value_to_letter
from core.services import (
    add_grade,
    create_course,
    create_student,
    enroll_student,
    get_average,
    get_average_letter,
    get_course_students,
    get_grades,
    get_grades_as_letters,
    get_report_card,
    get_student_courses,
)


@pytest.mark.django_db
class TestCreateEntities:
    def test_create_student(self):
        student = create_student("Alice")
        assert student.name == "Alice"
        assert student.pk is not None

    def test_create_course(self):
        course = create_course("Math")
        assert course.name == "Math"
        assert course.pk is not None


@pytest.mark.django_db
class TestEnrollment:
    def test_enroll_student(self):
        student = create_student("Alice")
        course = create_course("Math")
        enrollment = enroll_student(student, course)
        assert enrollment.student == student
        assert enrollment.course == course

    def test_enroll_student_duplicate(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        with pytest.raises(AlreadyEnrolledError):
            enroll_student(student, course)


@pytest.mark.django_db
class TestListings:
    def test_get_student_courses(self):
        student = create_student("Alice")
        math = create_course("Math")
        physics = create_course("Physics")
        enroll_student(student, math)
        enroll_student(student, physics)
        courses = get_student_courses(student)
        assert set(courses.values_list("name", flat=True)) == {"Math", "Physics"}

    def test_get_course_students(self):
        alice = create_student("Alice")
        bob = create_student("Bob")
        math = create_course("Math")
        enroll_student(alice, math)
        enroll_student(bob, math)
        students = get_course_students(math)
        assert set(students.values_list("name", flat=True)) == {"Alice", "Bob"}


@pytest.mark.django_db
class TestAddGrade:
    def test_add_grade_numeric(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        grade = add_grade(student, course, value=95)
        assert grade.value == 95

    def test_add_grade_letter(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        grade = add_grade(student, course, letter="A")
        assert grade.value == 96  # max of A range

    def test_add_grade_both_raises(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        with pytest.raises(InvalidGradeError):
            add_grade(student, course, value=95, letter="A")

    def test_add_grade_neither_raises(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        with pytest.raises(InvalidGradeError):
            add_grade(student, course)

    def test_add_grade_not_enrolled(self):
        student = create_student("Alice")
        course = create_course("Math")
        with pytest.raises(NotEnrolledError):
            add_grade(student, course, value=95)

    def test_add_grade_invalid_value(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        with pytest.raises(InvalidGradeError):
            add_grade(student, course, value=101)

    def test_add_grade_invalid_letter(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        with pytest.raises(InvalidGradeError):
            add_grade(student, course, letter="Z")


@pytest.mark.django_db
class TestGetGrades:
    def test_get_grades(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        add_grade(student, course, value=90)
        add_grade(student, course, value=85)
        assert get_grades(student, course) == [90, 85]

    def test_get_grades_as_letters(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        add_grade(student, course, value=95)
        add_grade(student, course, value=85)
        assert get_grades_as_letters(student, course) == ["A", "B"]


@pytest.mark.django_db
class TestAverage:
    def test_get_average(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        add_grade(student, course, value=90)
        add_grade(student, course, value=80)
        assert get_average(student, course) == 85

    def test_get_average_rounds(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        add_grade(student, course, value=90)
        add_grade(student, course, value=81)
        # (90 + 81) / 2 = 85.5 -> rounds to 86
        assert get_average(student, course) == 86

    def test_get_average_letter(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        add_grade(student, course, value=90)
        add_grade(student, course, value=80)
        # average = 85 -> B
        assert get_average_letter(student, course) == "B"

    def test_get_average_no_grades(self):
        student = create_student("Alice")
        course = create_course("Math")
        enroll_student(student, course)
        assert get_average(student, course) == 0


@pytest.mark.django_db
class TestReportCard:
    def test_report_card(self):
        student = create_student("Alice")
        math = create_course("Math")
        physics = create_course("Physics")
        enroll_student(student, math)
        enroll_student(student, physics)
        add_grade(student, math, value=95)
        add_grade(student, math, value=85)
        add_grade(student, physics, value=70)

        report = get_report_card(student)
        assert len(report) == 2

        by_course = {r["course"]: r for r in report}
        assert by_course["Math"]["grades"] == [95, 85]
        assert by_course["Math"]["average"] == 90
        assert by_course["Math"]["letter"] == "A-"
        assert by_course["Physics"]["grades"] == [70]
        assert by_course["Physics"]["average"] == 70
        assert by_course["Physics"]["letter"] == "C-"


class TestGradeScale:
    def test_value_to_letter(self):
        assert value_to_letter(100) == "A+"
        assert value_to_letter(97) == "A+"
        assert value_to_letter(93) == "A"
        assert value_to_letter(90) == "A-"
        assert value_to_letter(87) == "B+"
        assert value_to_letter(83) == "B"
        assert value_to_letter(80) == "B-"
        assert value_to_letter(77) == "C+"
        assert value_to_letter(73) == "C"
        assert value_to_letter(70) == "C-"
        assert value_to_letter(65) == "D"
        assert value_to_letter(50) == "F"
        assert value_to_letter(0) == "F"

    def test_letter_to_value(self):
        assert letter_to_value("A+") == 100
        assert letter_to_value("A") == 96
        assert letter_to_value("F") == 59

    def test_invalid_letter(self):
        with pytest.raises(ValueError):
            letter_to_value("Z")
