# API Acadêmica

API REST desenvolvida em **Django 5.2** para gerenciamento acadêmico de alunos, cursos, matrículas e notas.

---

## Tecnologias

| Tecnologia | Versão |
|---|---|
| Python | 3.10 |
| Django | 5.2 |
| Banco de Dados | SQLite3 |
| Testes | pytest + pytest-django |
| CI/CD | GitHub Actions |
| Container | Docker + Docker Compose |

---

## Estrutura do Projeto

```
api/
├── src/
│   ├── academic/           # Configuração do projeto Django
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── core/               # App principal
│       ├── models.py        # Modelos de dados
│       ├── views.py         # Endpoints da API
│       ├── services.py      # Regras de negócio
│       ├── grades.py        # Conversão de notas (número ↔ letra)
│       ├── exceptions.py    # Exceções customizadas
│       └── urls.py          # Roteamento da API
├── tests/
│   ├── tests.py             # Testes unitários e de integração
│   └── tests_integration.py # Testes de API (end-to-end)
├── docker/
│   └── entrypoint.sh
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pytest.ini
```

---

## Modelos de Dados

### Aluno
| Campo | Tipo | Descrição |
|---|---|---|
| id | AutoField | Identificador único |
| nome | CharField(200) | Nome do aluno |

### Curso
| Campo | Tipo | Descrição |
|---|---|---|
| id | AutoField | Identificador único |
| nome | CharField(200) | Nome do curso |

### Matrícula
| Campo | Tipo | Descrição |
|---|---|---|
| id | AutoField | Identificador único |
| aluno | ForeignKey(Aluno) | Referência ao aluno |
| curso | ForeignKey(Curso) | Referência ao curso |

> Restrição: um aluno não pode ser matriculado duas vezes no mesmo curso (`unique_together`).

### Nota
| Campo | Tipo | Descrição |
|---|---|---|
| id | AutoField | Identificador único |
| matricula | ForeignKey(Matrícula) | Referência à matrícula |
| valor | IntegerField | Valor numérico (0-100) |
| criado_em | DateTimeField | Data/hora de criação |

---

## Endpoints da API

Base URL: `http://localhost:8000/api/`

### Criar Aluno
```
POST /api/alunos/
Content-Type: application/json

{"nome": "João Silva"}
```
**Resposta (201):**
```json
{"id": 1, "nome": "João Silva"}
```

---

### Criar Curso
```
POST /api/cursos/
Content-Type: application/json

{"nome": "Matemática"}
```
**Resposta (201):**
```json
{"id": 1, "nome": "Matemática"}
```

---

### Matricular Aluno
```
POST /api/matriculas/
Content-Type: application/json

{"aluno_id": 1, "curso_id": 1}
```
**Resposta (201):**
```json
{"id": 1, "aluno_id": 1, "curso_id": 1}
```
**Erro (409):** aluno já matriculado no curso.

---

### Listar Cursos de um Aluno
```
GET /api/alunos/{aluno_id}/cursos/
```
**Resposta (200):**
```json
{"cursos": [{"id": 1, "nome": "Matemática"}]}
```

---

### Listar Alunos de um Curso
```
GET /api/cursos/{curso_id}/alunos/
```
**Resposta (200):**
```json
{"alunos": [{"id": 1, "nome": "João Silva"}]}
```

---

### Adicionar Nota
Aceita nota numérica (`valor`) ou por letra (`letra`).

```
POST /api/notas/
Content-Type: application/json

{"aluno_id": 1, "curso_id": 1, "valor": 85}
```
Ou por letra:
```json
{"aluno_id": 1, "curso_id": 1, "letra": "B"}
```
**Resposta (201):**
```json
{"id": 1, "valor": 85}
```
**Erro (400):** nota inválida. **Erro (404):** aluno não matriculado no curso.

---

### Listar Notas de um Aluno em um Curso
```
GET /api/alunos/{aluno_id}/cursos/{curso_id}/notas/
```
**Resposta (200):**
```json
{
  "notas": [
    {"valor": 85, "letra": "B", "criado_em": "2026-02-26T10:00:00Z"}
  ]
}
```

---

### Obter Boletim do Aluno
```
GET /api/alunos/{aluno_id}/boletim/
```
**Resposta (200):**
```json
{
  "aluno": "João Silva",
  "boletim": [
    {
      "curso": "Matemática",
      "notas": [{"valor": 85, "letra": "B"}],
      "media": 85,
      "media_letra": "B"
    }
  ]
}
```

---

## Escala de Notas

| Letra | Faixa Numérica |
|---|---|
| A+ | 97 - 100 |
| A  | 93 - 96 |
| A- | 90 - 92 |
| B+ | 87 - 89 |
| B  | 83 - 86 |
| B- | 80 - 82 |
| C+ | 77 - 79 |
| C  | 73 - 76 |
| C- | 70 - 72 |
| D  | 60 - 69 |
| F  | 0 - 59 |

---

## Tratamento de Erros

| Código HTTP | Significado | Exemplo |
|---|---|---|
| 400 | Requisição inválida | Campo obrigatório ausente, nota fora do intervalo |
| 404 | Recurso não encontrado | Aluno ou curso inexistente, aluno não matriculado |
| 409 | Conflito | Aluno já matriculado no mesmo curso |

Todas as respostas de erro seguem o formato:
```json
{"erro": "Mensagem descritiva do erro"}
```

---

## Como Executar

### Localmente
```bash
pip install -r requirements.txt
python src/manage.py migrate --run-syncdb
python src/manage.py runserver
```

### Com Docker
```bash
# Subir a aplicação (porta 8000)
docker-compose up app

# Rodar os testes
docker-compose run test
```

---

## Como Rodar os Testes

```bash
# Localmente
python -m pytest tests/ -v

# Via Docker
docker-compose run test
```

A suíte de testes cobre:
- Criação de entidades (alunos e cursos)
- Matrícula e prevenção de duplicatas
- Adição e consulta de notas (numérica e por letra)
- Cálculo de médias
- Geração de boletim
- Conversão entre escala numérica e por letra
- Fluxo completo end-to-end via API
- Cenários de erro (404, 409, 400)

---

## CI/CD

O projeto possui integração contínua via **GitHub Actions** que executa automaticamente os testes em todo push ou pull request na branch `master`, usando Python 3.10.
