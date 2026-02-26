import logging

ESCALA_NOTAS = [
    ("A+", 97, 100),
    ("A", 93, 96),
    ("A-", 90, 92),
    ("B+", 87, 89),
    ("B", 83, 86),
    ("B-", 80, 82),
    ("C+", 77, 79),
    ("C", 73, 76),
    ("C-", 70, 72),
    ("D", 60, 69),
    ("F", 0, 59),
]

_LETRA_PARA_MAXIMO = {letra: valor_maximo for letra, _, valor_maximo in ESCALA_NOTAS}
logger = logging.getLogger("core")


def valor_para_letra(valor):
    logger.info("[notas.valor_para_letra] inicio valor=%s", valor)
    for letra, valor_minimo, valor_maximo in ESCALA_NOTAS:
        if valor_minimo <= valor <= valor_maximo:
            logger.info("[notas.valor_para_letra] fim letra=%s", letra)
            return letra
    logger.warning("[notas.valor_para_letra] valor_fora_intervalo valor=%s", valor)
    raise ValueError(f"Valor da nota {valor} fora do intervalo 0-100")


def letra_para_valor(letra):
    logger.info("[notas.letra_para_valor] inicio letra=%s", letra)
    if letra not in _LETRA_PARA_MAXIMO:
        logger.warning("[notas.letra_para_valor] letra_invalida letra=%s", letra)
        raise ValueError(f"Nota em letra desconhecida: {letra}")
    valor = _LETRA_PARA_MAXIMO[letra]
    logger.info("[notas.letra_para_valor] fim valor=%s", valor)
    return valor
