from django.urls import path

from core import views

urlpatterns = [
    path("alunos/", views.criar_aluno_view, name="criar-aluno"),
    path("cursos/", views.criar_curso_view, name="criar-curso"),
    path("matriculas/", views.criar_matricula, name="criar-matricula"),
    path("alunos/<int:aluno_id>/cursos/", views.listar_cursos_aluno, name="listar-cursos-aluno"),
    path("cursos/<int:curso_id>/alunos/", views.listar_alunos_curso, name="listar-alunos-curso"),
    path("notas/", views.criar_nota, name="criar-nota"),
    path(
        "alunos/<int:aluno_id>/cursos/<int:curso_id>/notas/",
        views.listar_notas_aluno_curso,
        name="listar-notas-aluno-curso",
    ),
    path("alunos/<int:aluno_id>/boletim/", views.obter_boletim_aluno, name="obter-boletim-aluno"),
]
