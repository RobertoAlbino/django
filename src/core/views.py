import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from core.exceptions import ErroJaMatriculado, ErroNaoMatriculado, ErroNotaInvalida
from core.models import Aluno, Curso
from core.services import (
    adicionar_nota,
    criar_aluno,
    criar_curso,
    matricular_aluno,
    obter_alunos_curso,
    obter_boletim,
    obter_cursos_aluno,
    obter_notas,
)

logger = logging.getLogger("core")


def _carregar_json(requisicao):
    try:
        dados = json.loads(requisicao.body)
        logger.info("[views._carregar_json] payload_valido")
        return dados
    except (json.JSONDecodeError, ValueError):
        logger.warning("[views._carregar_json] payload_invalido")
        return None


@csrf_exempt
@require_POST
def criar_aluno_view(requisicao):
    logger.info("[views.criar_aluno] inicio")
    dados = _carregar_json(requisicao)
    if not dados or "nome" not in dados:
        logger.warning("[views.criar_aluno] erro campo_nome_ausente")
        return JsonResponse({"erro": "Campo 'nome' e obrigatorio"}, status=400)

    logger.info("[views.criar_aluno] criando nome=%s", dados["nome"])
    aluno = criar_aluno(dados["nome"])
    logger.info("[views.criar_aluno] criado id=%d nome=%s", aluno.pk, aluno.nome)
    return JsonResponse({"id": aluno.pk, "nome": aluno.nome}, status=201)


@csrf_exempt
@require_POST
def criar_curso_view(requisicao):
    logger.info("[views.criar_curso] inicio")
    dados = _carregar_json(requisicao)
    if not dados or "nome" not in dados:
        logger.warning("[views.criar_curso] erro campo_nome_ausente")
        return JsonResponse({"erro": "Campo 'nome' e obrigatorio"}, status=400)

    logger.info("[views.criar_curso] criando nome=%s", dados["nome"])
    curso = criar_curso(dados["nome"])
    logger.info("[views.criar_curso] criado id=%d nome=%s", curso.pk, curso.nome)
    return JsonResponse({"id": curso.pk, "nome": curso.nome}, status=201)


@csrf_exempt
@require_POST
def criar_matricula(requisicao):
    logger.info("[views.criar_matricula] inicio")
    dados = _carregar_json(requisicao)
    if not dados or "aluno_id" not in dados or "curso_id" not in dados:
        logger.warning("[views.criar_matricula] erro campos_obrigatorios_ausentes")
        return JsonResponse(
            {"erro": "Campos 'aluno_id' e 'curso_id' sao obrigatorios"}, status=400
        )

    try:
        aluno = Aluno.objects.get(pk=dados["aluno_id"])
    except Aluno.DoesNotExist:
        logger.warning("[views.criar_matricula] aluno_nao_encontrado id=%s", dados.get("aluno_id"))
        return JsonResponse({"erro": "Aluno nao encontrado"}, status=404)

    try:
        curso = Curso.objects.get(pk=dados["curso_id"])
    except Curso.DoesNotExist:
        logger.warning("[views.criar_matricula] curso_nao_encontrado id=%s", dados.get("curso_id"))
        return JsonResponse({"erro": "Curso nao encontrado"}, status=404)

    logger.info("[views.criar_matricula] matriculando aluno=%s curso=%s", aluno.nome, curso.nome)
    try:
        matricula = matricular_aluno(aluno, curso)
    except ErroJaMatriculado as erro:
        logger.warning("[views.criar_matricula] matricula_duplicada: %s", erro)
        return JsonResponse({"erro": str(erro)}, status=409)

    logger.info("[views.criar_matricula] matricula_criada id=%d", matricula.pk)
    return JsonResponse(
        {
            "id": matricula.pk,
            "aluno_id": aluno.pk,
            "curso_id": curso.pk,
        },
        status=201,
    )


@require_GET
def listar_cursos_aluno(requisicao, aluno_id):
    logger.info("[views.listar_cursos_aluno] inicio aluno_id=%s", aluno_id)
    try:
        aluno = Aluno.objects.get(pk=aluno_id)
    except Aluno.DoesNotExist:
        logger.warning("[views.listar_cursos_aluno] aluno_nao_encontrado id=%s", aluno_id)
        return JsonResponse({"erro": "Aluno nao encontrado"}, status=404)

    logger.info("[views.listar_cursos_aluno] buscando cursos do aluno=%s", aluno.nome)
    cursos = obter_cursos_aluno(aluno)
    resultado = [{"id": curso.pk, "nome": curso.nome} for curso in cursos]
    logger.info("[views.listar_cursos_aluno] total=%d", len(resultado))
    return JsonResponse({"cursos": resultado})


@require_GET
def listar_alunos_curso(requisicao, curso_id):
    logger.info("[views.listar_alunos_curso] inicio curso_id=%s", curso_id)
    try:
        curso = Curso.objects.get(pk=curso_id)
    except Curso.DoesNotExist:
        logger.warning("[views.listar_alunos_curso] curso_nao_encontrado id=%s", curso_id)
        return JsonResponse({"erro": "Curso nao encontrado"}, status=404)

    logger.info("[views.listar_alunos_curso] buscando alunos do curso=%s", curso.nome)
    alunos = obter_alunos_curso(curso)
    resultado = [{"id": aluno.pk, "nome": aluno.nome} for aluno in alunos]
    logger.info("[views.listar_alunos_curso] total=%d", len(resultado))
    return JsonResponse({"alunos": resultado})


@csrf_exempt
@require_POST
def criar_nota(requisicao):
    logger.info("[views.criar_nota] inicio")
    dados = _carregar_json(requisicao)
    if not dados or "aluno_id" not in dados or "curso_id" not in dados:
        logger.warning("[views.criar_nota] erro campos_obrigatorios_ausentes")
        return JsonResponse(
            {"erro": "Campos 'aluno_id' e 'curso_id' sao obrigatorios"}, status=400
        )

    try:
        aluno = Aluno.objects.get(pk=dados["aluno_id"])
    except Aluno.DoesNotExist:
        logger.warning("[views.criar_nota] aluno_nao_encontrado id=%s", dados.get("aluno_id"))
        return JsonResponse({"erro": "Aluno nao encontrado"}, status=404)

    try:
        curso = Curso.objects.get(pk=dados["curso_id"])
    except Curso.DoesNotExist:
        logger.warning("[views.criar_nota] curso_nao_encontrado id=%s", dados.get("curso_id"))
        return JsonResponse({"erro": "Curso nao encontrado"}, status=404)

    valor = dados.get("valor")
    letra = dados.get("letra")

    logger.info(
        "[views.criar_nota] adicionando aluno=%s curso=%s (valor=%s, letra=%s)",
        aluno.nome,
        curso.nome,
        valor,
        letra,
    )

    try:
        nota = adicionar_nota(aluno, curso, valor=valor, letra=letra)
    except ErroNaoMatriculado as erro:
        logger.warning("[views.criar_nota] falha_nao_matriculado: %s", erro)
        return JsonResponse({"erro": str(erro)}, status=404)
    except ErroNotaInvalida as erro:
        logger.warning("[views.criar_nota] falha_nota_invalida: %s", erro)
        return JsonResponse({"erro": str(erro)}, status=400)

    logger.info("[views.criar_nota] nota_criada id=%d valor=%d", nota.pk, nota.valor)
    return JsonResponse({"id": nota.pk, "valor": nota.valor}, status=201)


@require_GET
def listar_notas_aluno_curso(requisicao, aluno_id, curso_id):
    logger.info(
        "[views.listar_notas_aluno_curso] inicio aluno_id=%s curso_id=%s",
        aluno_id,
        curso_id,
    )
    try:
        aluno = Aluno.objects.get(pk=aluno_id)
    except Aluno.DoesNotExist:
        logger.warning("[views.listar_notas_aluno_curso] aluno_nao_encontrado id=%s", aluno_id)
        return JsonResponse({"erro": "Aluno nao encontrado"}, status=404)

    try:
        curso = Curso.objects.get(pk=curso_id)
    except Curso.DoesNotExist:
        logger.warning("[views.listar_notas_aluno_curso] curso_nao_encontrado id=%s", curso_id)
        return JsonResponse({"erro": "Curso nao encontrado"}, status=404)

    logger.info(
        "[views.listar_notas_aluno_curso] buscando notas aluno=%s curso=%s",
        aluno.nome,
        curso.nome,
    )

    try:
        notas = obter_notas(aluno, curso)
    except ErroNaoMatriculado as erro:
        logger.warning("[views.listar_notas_aluno_curso] aluno_nao_matriculado: %s", erro)
        return JsonResponse({"erro": str(erro)}, status=404)

    logger.info("[views.listar_notas_aluno_curso] total=%d", len(notas))
    return JsonResponse({"notas": notas})


@require_GET
def obter_boletim_aluno(requisicao, aluno_id):
    logger.info("[views.obter_boletim_aluno] inicio aluno_id=%s", aluno_id)
    try:
        aluno = Aluno.objects.get(pk=aluno_id)
    except Aluno.DoesNotExist:
        logger.warning("[views.obter_boletim_aluno] aluno_nao_encontrado id=%s", aluno_id)
        return JsonResponse({"erro": "Aluno nao encontrado"}, status=404)

    logger.info("[views.obter_boletim_aluno] gerando boletim aluno=%s", aluno.nome)
    boletim = obter_boletim(aluno)
    logger.info("[views.obter_boletim_aluno] total_cursos=%d", len(boletim))
    return JsonResponse({"aluno": aluno.nome, "boletim": boletim})
