from django.urls import path

from core import views

urlpatterns = [
    path("students/", views.student_create, name="student-create"),
    path("courses/", views.course_create, name="course-create"),
    path("enrollments/", views.enrollment_create, name="enrollment-create"),
    path("students/<int:student_id>/courses/", views.student_courses, name="student-courses"),
    path("courses/<int:course_id>/students/", views.course_students, name="course-students"),
    path("grades/", views.grade_create, name="grade-create"),
    path(
        "students/<int:student_id>/courses/<int:course_id>/grades/",
        views.student_course_grades,
        name="student-course-grades",
    ),
    path("students/<int:student_id>/report/", views.student_report, name="student-report"),
]
