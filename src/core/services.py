import logging

from django.db import IntegrityError

from core.exceptions import ErroJaMatriculado, ErroNaoMatriculado, ErroNotaInvalida
from core.grades import letra_para_valor, valor_para_letra
from core.models import Aluno, Curso, Matricula, Nota

logger = logging.getLogger("core")


def criar_aluno(nome):
    logger.info("[servicos.criar_aluno] inicio nome=%s", nome)
    aluno = Aluno.objects.create(nome=nome)
    logger.info("[servicos.criar_aluno] fim id=%s", aluno.pk)
    return aluno


def criar_curso(nome):
    logger.info("[servicos.criar_curso] inicio nome=%s", nome)
    curso = Curso.objects.create(nome=nome)
    logger.info("[servicos.criar_curso] fim id=%s", curso.pk)
    return curso


def matricular_aluno(aluno, curso):
    logger.info(
        "[servicos.matricular_aluno] inicio aluno_id=%s curso_id=%s",
        aluno.pk,
        curso.pk,
    )
    try:
        matricula = Matricula.objects.create(aluno=aluno, curso=curso)
        logger.info("[servicos.matricular_aluno] fim matricula_id=%s", matricula.pk)
        return matricula
    except IntegrityError:
        logger.warning(
            "[servicos.matricular_aluno] duplicado aluno_id=%s curso_id=%s",
            aluno.pk,
            curso.pk,
        )
        raise ErroJaMatriculado(
            f"{aluno.nome} ja esta matriculado em {curso.nome}"
        )


def _obter_matricula(aluno, curso):
    logger.info(
        "[servicos._obter_matricula] buscando aluno_id=%s curso_id=%s",
        aluno.pk,
        curso.pk,
    )
    try:
        matricula = Matricula.objects.get(aluno=aluno, curso=curso)
        logger.info("[servicos._obter_matricula] encontrada id=%s", matricula.pk)
        return matricula
    except Matricula.DoesNotExist:
        logger.warning(
            "[servicos._obter_matricula] nao_encontrada aluno_id=%s curso_id=%s",
            aluno.pk,
            curso.pk,
        )
        raise ErroNaoMatriculado(
            f"{aluno.nome} nao esta matriculado em {curso.nome}"
        )


def obter_cursos_aluno(aluno):
    logger.info("[servicos.obter_cursos_aluno] aluno_id=%s", aluno.pk)
    cursos = Curso.objects.filter(matriculas__aluno=aluno)
    logger.info("[servicos.obter_cursos_aluno] total=%s", cursos.count())
    return cursos


def obter_alunos_curso(curso):
    logger.info("[servicos.obter_alunos_curso] curso_id=%s", curso.pk)
    alunos = Aluno.objects.filter(matriculas__curso=curso)
    logger.info("[servicos.obter_alunos_curso] total=%s", alunos.count())
    return alunos


def adicionar_nota(aluno, curso, valor=None, letra=None):
    logger.info(
        "[servicos.adicionar_nota] inicio aluno_id=%s curso_id=%s valor=%s letra=%s",
        aluno.pk,
        curso.pk,
        valor,
        letra,
    )
    if valor is not None and letra is not None:
        logger.warning("[servicos.adicionar_nota] erro valor_e_letra_juntos")
        raise ErroNotaInvalida("Informe valor ou letra, nao ambos")
    if valor is None and letra is None:
        logger.warning("[servicos.adicionar_nota] erro valor_e_letra_ausentes")
        raise ErroNotaInvalida("Informe valor ou letra")

    if letra is not None:
        try:
            valor = letra_para_valor(letra)
            logger.info("[servicos.adicionar_nota] letra_convertida valor=%s", valor)
        except ValueError:
            logger.warning("[servicos.adicionar_nota] erro letra_invalida=%s", letra)
            raise ErroNotaInvalida(f"Nota em letra invalida: {letra}")

    if not (0 <= valor <= 100):
        logger.warning("[servicos.adicionar_nota] erro valor_fora_intervalo valor=%s", valor)
        raise ErroNotaInvalida(f"Valor da nota deve estar entre 0 e 100, recebido {valor}")

    matricula = _obter_matricula(aluno, curso)
    nota = Nota.objects.create(matricula=matricula, valor=valor)
    logger.info("[servicos.adicionar_nota] fim nota_id=%s", nota.pk)
    return nota


def obter_notas(aluno, curso):
    logger.info(
        "[servicos.obter_notas] inicio aluno_id=%s curso_id=%s",
        aluno.pk,
        curso.pk,
    )
    matricula = _obter_matricula(aluno, curso)
    notas = list(matricula.notas.order_by("criado_em").values_list("valor", flat=True))
    logger.info("[servicos.obter_notas] fim total=%s", len(notas))
    return notas


def obter_notas_como_letras(aluno, curso):
    logger.info(
        "[servicos.obter_notas_como_letras] inicio aluno_id=%s curso_id=%s",
        aluno.pk,
        curso.pk,
    )
    notas_como_letras = [valor_para_letra(valor) for valor in obter_notas(aluno, curso)]
    logger.info(
        "[servicos.obter_notas_como_letras] fim total=%s",
        len(notas_como_letras),
    )
    return notas_como_letras


def obter_media(aluno, curso):
    logger.info(
        "[servicos.obter_media] inicio aluno_id=%s curso_id=%s",
        aluno.pk,
        curso.pk,
    )
    notas = obter_notas(aluno, curso)
    if not notas:
        logger.info("[servicos.obter_media] sem_notas retorno=0")
        return 0
    media = round(sum(notas) / len(notas))
    logger.info("[servicos.obter_media] fim media=%s", media)
    return media


def obter_media_em_letra(aluno, curso):
    logger.info(
        "[servicos.obter_media_em_letra] inicio aluno_id=%s curso_id=%s",
        aluno.pk,
        curso.pk,
    )
    media_em_letra = valor_para_letra(obter_media(aluno, curso))
    logger.info("[servicos.obter_media_em_letra] fim letra=%s", media_em_letra)
    return media_em_letra


def obter_boletim(aluno):
    logger.info("[servicos.obter_boletim] inicio aluno_id=%s", aluno.pk)
    matriculas = Matricula.objects.filter(aluno=aluno).select_related("curso")
    boletim = []
    for matricula in matriculas:
        logger.info(
            "[servicos.obter_boletim] processando matricula_id=%s curso=%s",
            matricula.pk,
            matricula.curso.nome,
        )
        notas = list(matricula.notas.order_by("criado_em").values_list("valor", flat=True))
        media = round(sum(notas) / len(notas)) if notas else 0
        boletim.append(
            {
                "curso": matricula.curso.nome,
                "notas": notas,
                "media": media,
                "letra": valor_para_letra(media),
            }
        )
    logger.info("[servicos.obter_boletim] fim total_cursos=%s", len(boletim))
    return boletim
