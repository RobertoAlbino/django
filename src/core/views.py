import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from core.exceptions import AlreadyEnrolledError, InvalidGradeError, NotEnrolledError
from core.models import Course, Student
from core.services import (
    add_grade,
    create_course,
    create_student,
    enroll_student,
    get_course_students,
    get_grades,
    get_report_card,
    get_student_courses,
)

logger = logging.getLogger("core")


def _parse_json(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return None


@csrf_exempt
@require_POST
def student_create(request):
    data = _parse_json(request)
    if not data or "name" not in data:
        return JsonResponse({"error": "Field 'name' is required"}, status=400)

    logger.info("Creating student: %s", data["name"])
    student = create_student(data["name"])
    logger.info("Student created: id=%d, name=%s", student.pk, student.name)
    return JsonResponse({"id": student.pk, "name": student.name}, status=201)


@csrf_exempt
@require_POST
def course_create(request):
    data = _parse_json(request)
    if not data or "name" not in data:
        return JsonResponse({"error": "Field 'name' is required"}, status=400)

    logger.info("Creating course: %s", data["name"])
    course = create_course(data["name"])
    logger.info("Course created: id=%d, name=%s", course.pk, course.name)
    return JsonResponse({"id": course.pk, "name": course.name}, status=201)


@csrf_exempt
@require_POST
def enrollment_create(request):
    data = _parse_json(request)
    if not data or "student_id" not in data or "course_id" not in data:
        return JsonResponse(
            {"error": "Fields 'student_id' and 'course_id' are required"}, status=400
        )

    try:
        student = Student.objects.get(pk=data["student_id"])
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    try:
        course = Course.objects.get(pk=data["course_id"])
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    logger.info("Enrolling student=%s in course=%s", student.name, course.name)
    try:
        enrollment = enroll_student(student, course)
    except AlreadyEnrolledError as e:
        logger.warning("Duplicate enrollment: %s", e)
        return JsonResponse({"error": str(e)}, status=409)

    logger.info("Enrollment created: id=%d", enrollment.pk)
    return JsonResponse(
        {
            "id": enrollment.pk,
            "student_id": student.pk,
            "course_id": course.pk,
        },
        status=201,
    )


@require_GET
def student_courses(request, student_id):
    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    logger.info("Listing courses for student=%s", student.name)
    courses = get_student_courses(student)
    result = [{"id": c.pk, "name": c.name} for c in courses]
    logger.info("Found %d courses for student=%s", len(result), student.name)
    return JsonResponse({"courses": result})


@require_GET
def course_students(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    logger.info("Listing students for course=%s", course.name)
    students = get_course_students(course)
    result = [{"id": s.pk, "name": s.name} for s in students]
    logger.info("Found %d students in course=%s", len(result), course.name)
    return JsonResponse({"students": result})


@csrf_exempt
@require_POST
def grade_create(request):
    data = _parse_json(request)
    if not data or "student_id" not in data or "course_id" not in data:
        return JsonResponse(
            {"error": "Fields 'student_id' and 'course_id' are required"}, status=400
        )

    try:
        student = Student.objects.get(pk=data["student_id"])
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    try:
        course = Course.objects.get(pk=data["course_id"])
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    value = data.get("value")
    letter = data.get("letter")

    logger.info(
        "Adding grade for student=%s, course=%s (value=%s, letter=%s)",
        student.name,
        course.name,
        value,
        letter,
    )

    try:
        grade = add_grade(student, course, value=value, letter=letter)
    except NotEnrolledError as e:
        logger.warning("Grade failed - not enrolled: %s", e)
        return JsonResponse({"error": str(e)}, status=404)
    except InvalidGradeError as e:
        logger.warning("Grade failed - invalid: %s", e)
        return JsonResponse({"error": str(e)}, status=400)

    logger.info("Grade added: id=%d, value=%d", grade.pk, grade.value)
    return JsonResponse({"id": grade.pk, "value": grade.value}, status=201)


@require_GET
def student_course_grades(request, student_id, course_id):
    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    try:
        course = Course.objects.get(pk=course_id)
    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found"}, status=404)

    logger.info(
        "Getting grades for student=%s, course=%s", student.name, course.name
    )

    try:
        grades = get_grades(student, course)
    except NotEnrolledError as e:
        return JsonResponse({"error": str(e)}, status=404)

    logger.info("Found %d grades", len(grades))
    return JsonResponse({"grades": grades})


@require_GET
def student_report(request, student_id):
    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        return JsonResponse({"error": "Student not found"}, status=404)

    logger.info("Generating report card for student=%s", student.name)
    report = get_report_card(student)
    logger.info("Report card: %d courses", len(report))
    return JsonResponse({"student": student.name, "report": report})
