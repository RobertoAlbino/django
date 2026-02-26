#!/usr/bin/env bash
set -u

BASE_URL="${BASE_URL:-http://127.0.0.1:8000/api}"
CONTENT_TYPE="Content-Type: application/json"
FAILURES=0
LAST_BODY=""
LAST_STATUS=""

info() {
  echo "[INFO] $*"
}

pass() {
  echo "[PASS] $*"
}

fail() {
  echo "[FAIL] $*" >&2
  FAILURES=$((FAILURES + 1))
}

json_get() {
  local chave="$1"
  python3 -c '
import json
import sys

chave = sys.argv[1]
try:
    valor = json.load(sys.stdin)
except Exception:
    sys.exit(1)

for parte in chave.split("."):
    if isinstance(valor, dict) and parte in valor:
        valor = valor[parte]
    else:
        sys.exit(1)

if valor is None:
    sys.exit(1)

print(valor)
' "$chave"
}

request() {
  local metodo="$1"
  local caminho="$2"
  local payload="$3"
  local esperado="$4"

  local url="${BASE_URL%/}${caminho}"
  local arq_body
  arq_body="$(mktemp)"

  local status
  if [[ -n "$payload" ]]; then
    status="$(curl -sS -o "$arq_body" -w "%{http_code}" -X "$metodo" "$url" -H "$CONTENT_TYPE" -d "$payload")"
  else
    status="$(curl -sS -o "$arq_body" -w "%{http_code}" -X "$metodo" "$url")"
  fi

  LAST_BODY="$(cat "$arq_body")"
  LAST_STATUS="$status"
  rm -f "$arq_body"

  if [[ "$status" == "$esperado" ]]; then
    pass "$metodo $caminho -> $status"
  else
    fail "$metodo $caminho -> esperado $esperado, recebido $status | body: $LAST_BODY"
    if [[ "$status" == "500" ]]; then
      fail "API retornou 500. Verifique migracoes/banco e logs do servidor."
    fi
  fi
}

require_id() {
  local id
  if ! id="$(printf '%s' "$LAST_BODY" | json_get "id" 2>/dev/null)"; then
    fail "Nao foi possivel extrair 'id' da resposta: $LAST_BODY"
    echo ""
    return
  fi
  echo "$id"
}

abort_if_empty() {
  local valor="$1"
  local nome="$2"
  if [[ -z "$valor" ]]; then
    fail "Abortando: $nome vazio por falha anterior."
    echo "== Resultado =="
    fail "Total de falhas: $FAILURES"
    exit 1
  fi
}

preflight_servidor() {
  local status
  status="$(curl -sS -o /dev/null -w "%{http_code}" "$BASE_URL/alunos/" || true)"
  if [[ "$status" == "000" ]]; then
    fail "API indisponivel em $BASE_URL (conexao recusada)."
    fail "Suba o servidor: python3 manage.py runserver 127.0.0.1:8000"
    exit 1
  fi
  info "Servidor respondeu no preflight com status $status"
}

info "Usando BASE_URL=$BASE_URL"
preflight_servidor

echo "== Fluxo principal =="
request "POST" "/alunos/" '{"nome":"Alice"}' "201"
ALUNO_ID="$(require_id)"
abort_if_empty "$ALUNO_ID" "ALUNO_ID"

request "POST" "/cursos/" '{"nome":"Matematica"}' "201"
CURSO_MAT_ID="$(require_id)"
abort_if_empty "$CURSO_MAT_ID" "CURSO_MAT_ID"

request "POST" "/cursos/" '{"nome":"Fisica"}' "201"
CURSO_FIS_ID="$(require_id)"
abort_if_empty "$CURSO_FIS_ID" "CURSO_FIS_ID"

request "POST" "/matriculas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_MAT_ID}" "201"
request "POST" "/matriculas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_FIS_ID}" "201"

request "POST" "/notas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_MAT_ID,\"valor\":95}" "201"
request "POST" "/notas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_MAT_ID,\"valor\":85}" "201"
request "POST" "/notas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_FIS_ID,\"letra\":\"B\"}" "201"

request "GET" "/alunos/$ALUNO_ID/cursos/" "" "200"
request "GET" "/cursos/$CURSO_MAT_ID/alunos/" "" "200"
request "GET" "/alunos/$ALUNO_ID/cursos/$CURSO_MAT_ID/notas/" "" "200"
request "GET" "/alunos/$ALUNO_ID/boletim/" "" "200"

echo "== Casos de erro =="
request "POST" "/matriculas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_MAT_ID}" "409"

request "POST" "/alunos/" '{"nome":"Bruno"}' "201"
ALUNO2_ID="$(require_id)"
abort_if_empty "$ALUNO2_ID" "ALUNO2_ID"

request "POST" "/cursos/" '{"nome":"Historia"}' "201"
CURSO2_ID="$(require_id)"
abort_if_empty "$CURSO2_ID" "CURSO2_ID"

request "POST" "/notas/" "{\"aluno_id\":$ALUNO2_ID,\"curso_id\":$CURSO2_ID,\"valor\":80}" "404"
request "POST" "/notas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_MAT_ID,\"valor\":101}" "400"
request "POST" "/notas/" "{\"aluno_id\":$ALUNO_ID,\"curso_id\":$CURSO_MAT_ID,\"letra\":\"Z\"}" "400"
request "GET" "/alunos/9999/cursos/" "" "404"
request "GET" "/cursos/9999/alunos/" "" "404"
request "POST" "/alunos/" '{}' "400"
request "POST" "/cursos/" '{}' "400"

echo "== Resultado =="
if [[ "$FAILURES" -eq 0 ]]; then
  pass "Todos os testes de curl passaram"
  exit 0
fi

fail "Total de falhas: $FAILURES"
exit 1
