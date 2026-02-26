from django.db import IntegrityError

from core.exceptions import AlreadyEnrolledError, InvalidGradeError, NotEnrolledError
from core.grades import letter_to_value, value_to_letter
from core.models import Course, Enrollment, Grade, Student


def create_student(name):
    return Student.objects.create(name=name)


def create_course(name):
    return Course.objects.create(name=name)


def enroll_student(student, course):
    try:
        return Enrollment.objects.create(student=student, course=course)
    except IntegrityError:
        raise AlreadyEnrolledError(
            f"{student.name} is already enrolled in {course.name}"
        )


def _get_enrollment(student, course):
    try:
        return Enrollment.objects.get(student=student, course=course)
    except Enrollment.DoesNotExist:
        raise NotEnrolledError(
            f"{student.name} is not enrolled in {course.name}"
        )


def get_student_courses(student):
    return Course.objects.filter(enrollments__student=student)


def get_course_students(course):
    return Student.objects.filter(enrollments__course=course)


def add_grade(student, course, value=None, letter=None):
    if value is not None and letter is not None:
        raise InvalidGradeError("Provide either value or letter, not both")
    if value is None and letter is None:
        raise InvalidGradeError("Provide either value or letter")

    if letter is not None:
        try:
            value = letter_to_value(letter)
        except ValueError:
            raise InvalidGradeError(f"Invalid letter grade: {letter}")

    if not (0 <= value <= 100):
        raise InvalidGradeError(f"Grade value must be between 0 and 100, got {value}")

    enrollment = _get_enrollment(student, course)
    return Grade.objects.create(enrollment=enrollment, value=value)


def get_grades(student, course):
    enrollment = _get_enrollment(student, course)
    return list(enrollment.grades.order_by("created_at").values_list("value", flat=True))


def get_grades_as_letters(student, course):
    return [value_to_letter(v) for v in get_grades(student, course)]


def get_average(student, course):
    grades = get_grades(student, course)
    if not grades:
        return 0
    return round(sum(grades) / len(grades))


def get_average_letter(student, course):
    return value_to_letter(get_average(student, course))


def get_report_card(student):
    enrollments = Enrollment.objects.filter(student=student).select_related("course")
    report = []
    for enrollment in enrollments:
        grades = list(
            enrollment.grades.order_by("created_at").values_list("value", flat=True)
        )
        average = round(sum(grades) / len(grades)) if grades else 0
        report.append({
            "course": enrollment.course.name,
            "grades": grades,
            "average": average,
            "letter": value_to_letter(average),
        })
    return report
