import json
import logging

import pytest
from django.test import Client

logger = logging.getLogger("core")


@pytest.fixture
def client():
    return Client()


def _postar(cliente, url, dados):
    return cliente.post(url, json.dumps(dados), content_type="application/json")


@pytest.mark.django_db
class TestFluxoCompleto:
    """Teste do fluxo completo: criar aluno -> criar curso -> matricular -> adicionar notas -> consultar."""

    def test_fluxo_completo(self, client):
        logger.info("=== Iniciando teste de fluxo completo ===")

        resp = _postar(client, "/api/alunos/", {"nome": "Alice"})
        assert resp.status_code == 201
        aluno = resp.json()
        assert aluno["nome"] == "Alice"
        aluno_id = aluno["id"]

        resp = _postar(client, "/api/cursos/", {"nome": "Math"})
        assert resp.status_code == 201
        matematica = resp.json()
        matematica_id = matematica["id"]

        resp = _postar(client, "/api/cursos/", {"nome": "Physics"})
        assert resp.status_code == 201
        fisica = resp.json()
        fisica_id = fisica["id"]

        resp = _postar(
            client,
            "/api/matriculas/",
            {"aluno_id": aluno_id, "curso_id": matematica_id},
        )
        assert resp.status_code == 201

        resp = _postar(
            client,
            "/api/matriculas/",
            {"aluno_id": aluno_id, "curso_id": fisica_id},
        )
        assert resp.status_code == 201

        resp = _postar(
            client,
            "/api/notas/",
            {"aluno_id": aluno_id, "curso_id": matematica_id, "valor": 95},
        )
        assert resp.status_code == 201
        assert resp.json()["valor"] == 95

        resp = _postar(
            client,
            "/api/notas/",
            {"aluno_id": aluno_id, "curso_id": matematica_id, "valor": 85},
        )
        assert resp.status_code == 201

        resp = _postar(
            client,
            "/api/notas/",
            {"aluno_id": aluno_id, "curso_id": fisica_id, "letra": "B"},
        )
        assert resp.status_code == 201

        resp = client.get(f"/api/alunos/{aluno_id}/cursos/")
        assert resp.status_code == 200
        cursos = resp.json()["cursos"]
        assert len(cursos) == 2
        nomes_cursos = {c["nome"] for c in cursos}
        assert nomes_cursos == {"Math", "Physics"}

        resp = client.get(f"/api/cursos/{matematica_id}/alunos/")
        assert resp.status_code == 200
        alunos = resp.json()["alunos"]
        assert len(alunos) == 1
        assert alunos[0]["nome"] == "Alice"

        resp = client.get(f"/api/alunos/{aluno_id}/cursos/{matematica_id}/notas/")
        assert resp.status_code == 200
        assert resp.json()["notas"] == [95, 85]

        resp = client.get(f"/api/alunos/{aluno_id}/boletim/")
        assert resp.status_code == 200
        boletim_resposta = resp.json()
        assert boletim_resposta["aluno"] == "Alice"
        assert len(boletim_resposta["boletim"]) == 2

        por_curso = {item["curso"]: item for item in boletim_resposta["boletim"]}
        assert por_curso["Math"]["notas"] == [95, 85]
        assert por_curso["Math"]["media"] == 90
        assert por_curso["Math"]["letra"] == "A-"

        logger.info("=== Teste de fluxo completo concluido ===")


@pytest.mark.django_db
class TestCasosErro:
    """Testa respostas de erro da API."""

    def test_matricula_duplicada_retorna_409(self, client):
        resp = _postar(client, "/api/alunos/", {"nome": "Bob"})
        aluno_id = resp.json()["id"]

        resp = _postar(client, "/api/cursos/", {"nome": "History"})
        curso_id = resp.json()["id"]

        resp = _postar(
            client,
            "/api/matriculas/",
            {"aluno_id": aluno_id, "curso_id": curso_id},
        )
        assert resp.status_code == 201

        resp = _postar(
            client,
            "/api/matriculas/",
            {"aluno_id": aluno_id, "curso_id": curso_id},
        )
        assert resp.status_code == 409
        assert "matriculado" in resp.json()["erro"].lower()

    def test_nota_sem_matricula_retorna_404(self, client):
        resp = _postar(client, "/api/alunos/", {"nome": "Charlie"})
        aluno_id = resp.json()["id"]

        resp = _postar(client, "/api/cursos/", {"nome": "Art"})
        curso_id = resp.json()["id"]

        resp = _postar(
            client,
            "/api/notas/",
            {"aluno_id": aluno_id, "curso_id": curso_id, "valor": 80},
        )
        assert resp.status_code == 404
        assert "matriculado" in resp.json()["erro"].lower()

    def test_valor_nota_invalido_retorna_400(self, client):
        resp = _postar(client, "/api/alunos/", {"nome": "Diana"})
        aluno_id = resp.json()["id"]

        resp = _postar(client, "/api/cursos/", {"nome": "Music"})
        curso_id = resp.json()["id"]

        _postar(
            client,
            "/api/matriculas/",
            {"aluno_id": aluno_id, "curso_id": curso_id},
        )

        resp = _postar(
            client,
            "/api/notas/",
            {"aluno_id": aluno_id, "curso_id": curso_id, "valor": 101},
        )
        assert resp.status_code == 400

    def test_letra_nota_invalida_retorna_400(self, client):
        resp = _postar(client, "/api/alunos/", {"nome": "Eve"})
        aluno_id = resp.json()["id"]

        resp = _postar(client, "/api/cursos/", {"nome": "PE"})
        curso_id = resp.json()["id"]

        _postar(
            client,
            "/api/matriculas/",
            {"aluno_id": aluno_id, "curso_id": curso_id},
        )

        resp = _postar(
            client,
            "/api/notas/",
            {"aluno_id": aluno_id, "curso_id": curso_id, "letra": "Z"},
        )
        assert resp.status_code == 400

    def test_aluno_nao_encontrado_retorna_404(self, client):
        resp = client.get("/api/alunos/9999/cursos/")
        assert resp.status_code == 404

    def test_curso_nao_encontrado_retorna_404(self, client):
        resp = client.get("/api/cursos/9999/alunos/")
        assert resp.status_code == 404

    def test_nome_ausente_retorna_400(self, client):
        resp = _postar(client, "/api/alunos/", {})
        assert resp.status_code == 400

        resp = _postar(client, "/api/cursos/", {})
        assert resp.status_code == 400

    def test_notas_sem_matricula_retorna_404(self, client):
        resp = _postar(client, "/api/alunos/", {"nome": "Frank"})
        aluno_id = resp.json()["id"]

        resp = _postar(client, "/api/cursos/", {"nome": "Biology"})
        curso_id = resp.json()["id"]

        resp = client.get(f"/api/alunos/{aluno_id}/cursos/{curso_id}/notas/")
        assert resp.status_code == 404
