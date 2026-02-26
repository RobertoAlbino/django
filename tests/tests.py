import pytest

from core.exceptions import ErroJaMatriculado, ErroNaoMatriculado, ErroNotaInvalida
from core.grades import letra_para_valor, valor_para_letra
from core.services import (
    adicionar_nota,
    criar_aluno,
    criar_curso,
    matricular_aluno,
    obter_alunos_curso,
    obter_boletim,
    obter_cursos_aluno,
    obter_media,
    obter_media_em_letra,
    obter_notas,
    obter_notas_como_letras,
)


@pytest.mark.django_db
class TestCriacaoEntidades:
    def test_criar_aluno(self):
        aluno = criar_aluno("Alice")
        assert aluno.nome == "Alice"
        assert aluno.pk is not None

    def test_criar_curso(self):
        curso = criar_curso("Math")
        assert curso.nome == "Math"
        assert curso.pk is not None


@pytest.mark.django_db
class TestMatricula:
    def test_matricular_aluno(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricula = matricular_aluno(aluno, curso)
        assert matricula.aluno == aluno
        assert matricula.curso == curso

    def test_matricular_aluno_duplicado(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        with pytest.raises(ErroJaMatriculado):
            matricular_aluno(aluno, curso)


@pytest.mark.django_db
class TestListagens:
    def test_obter_cursos_aluno(self):
        aluno = criar_aluno("Alice")
        matematica = criar_curso("Math")
        fisica = criar_curso("Physics")
        matricular_aluno(aluno, matematica)
        matricular_aluno(aluno, fisica)
        cursos = obter_cursos_aluno(aluno)
        assert set(cursos.values_list("nome", flat=True)) == {"Math", "Physics"}

    def test_obter_alunos_curso(self):
        alice = criar_aluno("Alice")
        bob = criar_aluno("Bob")
        matematica = criar_curso("Math")
        matricular_aluno(alice, matematica)
        matricular_aluno(bob, matematica)
        alunos = obter_alunos_curso(matematica)
        assert set(alunos.values_list("nome", flat=True)) == {"Alice", "Bob"}


@pytest.mark.django_db
class TestAdicionarNota:
    def test_adicionar_nota_numerica(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        nota = adicionar_nota(aluno, curso, valor=95)
        assert nota.valor == 95

    def test_adicionar_nota_letra(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        nota = adicionar_nota(aluno, curso, letra="A")
        assert nota.valor == 96

    def test_adicionar_nota_valor_e_letra_gera_erro(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        with pytest.raises(ErroNotaInvalida):
            adicionar_nota(aluno, curso, valor=95, letra="A")

    def test_adicionar_nota_sem_valor_e_sem_letra_gera_erro(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        with pytest.raises(ErroNotaInvalida):
            adicionar_nota(aluno, curso)

    def test_adicionar_nota_sem_matricula(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        with pytest.raises(ErroNaoMatriculado):
            adicionar_nota(aluno, curso, valor=95)

    def test_adicionar_nota_valor_invalido(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        with pytest.raises(ErroNotaInvalida):
            adicionar_nota(aluno, curso, valor=101)

    def test_adicionar_nota_letra_invalida(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        with pytest.raises(ErroNotaInvalida):
            adicionar_nota(aluno, curso, letra="Z")


@pytest.mark.django_db
class TestObterNotas:
    def test_obter_notas(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        adicionar_nota(aluno, curso, valor=90)
        adicionar_nota(aluno, curso, valor=85)
        assert obter_notas(aluno, curso) == [90, 85]

    def test_obter_notas_como_letras(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        adicionar_nota(aluno, curso, valor=95)
        adicionar_nota(aluno, curso, valor=85)
        assert obter_notas_como_letras(aluno, curso) == ["A", "B"]


@pytest.mark.django_db
class TestMedia:
    def test_obter_media(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        adicionar_nota(aluno, curso, valor=90)
        adicionar_nota(aluno, curso, valor=80)
        assert obter_media(aluno, curso) == 85

    def test_obter_media_arredonda(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        adicionar_nota(aluno, curso, valor=90)
        adicionar_nota(aluno, curso, valor=81)
        assert obter_media(aluno, curso) == 86

    def test_obter_media_em_letra(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        adicionar_nota(aluno, curso, valor=90)
        adicionar_nota(aluno, curso, valor=80)
        assert obter_media_em_letra(aluno, curso) == "B"

    def test_obter_media_sem_notas(self):
        aluno = criar_aluno("Alice")
        curso = criar_curso("Math")
        matricular_aluno(aluno, curso)
        assert obter_media(aluno, curso) == 0


@pytest.mark.django_db
class TestBoletim:
    def test_obter_boletim(self):
        aluno = criar_aluno("Alice")
        matematica = criar_curso("Math")
        fisica = criar_curso("Physics")
        matricular_aluno(aluno, matematica)
        matricular_aluno(aluno, fisica)
        adicionar_nota(aluno, matematica, valor=95)
        adicionar_nota(aluno, matematica, valor=85)
        adicionar_nota(aluno, fisica, valor=70)

        boletim = obter_boletim(aluno)
        assert len(boletim) == 2

        por_curso = {item["curso"]: item for item in boletim}
        assert por_curso["Math"]["notas"] == [95, 85]
        assert por_curso["Math"]["media"] == 90
        assert por_curso["Math"]["letra"] == "A-"
        assert por_curso["Physics"]["notas"] == [70]
        assert por_curso["Physics"]["media"] == 70
        assert por_curso["Physics"]["letra"] == "C-"


class TestEscalaNotas:
    def test_valor_para_letra(self):
        assert valor_para_letra(100) == "A+"
        assert valor_para_letra(97) == "A+"
        assert valor_para_letra(93) == "A"
        assert valor_para_letra(90) == "A-"
        assert valor_para_letra(87) == "B+"
        assert valor_para_letra(83) == "B"
        assert valor_para_letra(80) == "B-"
        assert valor_para_letra(77) == "C+"
        assert valor_para_letra(73) == "C"
        assert valor_para_letra(70) == "C-"
        assert valor_para_letra(65) == "D"
        assert valor_para_letra(50) == "F"
        assert valor_para_letra(0) == "F"

    def test_letra_para_valor(self):
        assert letra_para_valor("A+") == 100
        assert letra_para_valor("A") == 96
        assert letra_para_valor("F") == 59

    def test_letra_invalida(self):
        with pytest.raises(ValueError):
            letra_para_valor("Z")
