# Corporate AI Assistant (RAG + Agents)

AI-агент для работы с внутренней базой знаний компании: пользователь загружает
документы, задаёт вопросы, агент ищет релевантный контекст через RAG, отвечает с
опорой на источники, при необходимости вызывает инструменты и сохраняет историю.

Демонстрационный инженерный проект под вакансии **AI Agent Developer /
AI Application Developer / AI Engineer**.

## Стек

Backend: Python 3.11+, FastAPI, Pydantic. LLM/Agents: LangChain, LangGraph,
Ollama (OpenAI-совместимый API). RAG: Chroma, nomic-embed-text. Хранилище:
PostgreSQL. Очереди: RabbitMQ. UI: Streamlit. DevOps: Docker Compose.

## Архитектура

```
                ┌─────────────┐
                │ Streamlit UI│  чат · документы · история · оценки
                └──────┬──────┘
                       │ REST
                ┌──────▼───────────────────────────────────────┐
                │                FastAPI                         │
                │  /chat   /documents   /sessions   /health      │
                └───┬───────────────┬──────────────────┬────────┘
       вопрос       │               │ upload           │ история
                    ▼               ▼                  ▼
            ┌───────────────┐  ┌──────────┐     ┌──────────────┐
            │ LangGraph     │  │ RabbitMQ │     │ PostgreSQL   │
            │ agent         │  │  queue   │     │ сессии/оценки│
            │ router→tool→  │  └────┬─────┘     └──────────────┘
            │ generate      │       │ задача
            └──────┬────────┘       ▼
        search_documents      ┌──────────┐
                    │         │  Worker   │ extract→chunk→embed
                    ▼         └────┬─────┘
            ┌──────────────────────▼───────┐
            │        Chroma (server)        │  векторный поиск
            └───────────────┬───────────────┘
                            ▼
                    ┌───────────────┐
                    │ Ollama (хост) │  qwen3:14b · nomic-embed-text
                    └───────────────┘
```

Поток вопроса: UI → FastAPI → LangGraph-агент (router решает search/direct) →
tool `search_documents` → Chroma → LLM генерирует ответ по контексту → ответ с
источниками + запись хода в PostgreSQL.

Поток загрузки: UI → FastAPI сохраняет файл и ставит задачу в RabbitMQ → Worker
извлекает текст, чанкует, считает эмбеддинги и пишет в Chroma → статус документа
обновляется в PostgreSQL.

## Прогресс по этапам

- [x] **Этап 1** — базовый backend: FastAPI, `/health`, `/chat`, подключение LLM (Ollama)
- [x] **Этап 2** — Streamlit UI: чат-экран, подключение к backend, история в сессии
- [x] **Этап 3** — документы и RAG: PDF/TXT/DOCX, chunking, эмбеддинги (nomic с префиксами), Chroma, источники
- [x] **Этап 4** — LangGraph-агент: граф состояний, router-нода, tool search_documents, маршрут search/direct
- [x] **Этап 5** — PostgreSQL: документы, сессии, сообщения, источники и оценки в БД; история и feedback
- [x] **Этап 6** — RabbitMQ + worker: асинхронная загрузка, очередь document_processing, статусы; Chroma в server-режиме
- [x] **Этап 7** — Docker Compose: backend, worker, frontend, postgres, rabbitmq, chroma одной командой
- [x] **Этап 8** — полировка: чистый код, тесты, диаграмма архитектуры, логирование

## Структура проекта

```
Corporate Assistant/
├── backend/
│   ├── app/
│   │   ├── main.py              # сборка FastAPI
│   │   ├── api/                 # роуты: chat, documents, sessions, health
│   │   ├── core/                # config (Pydantic Settings), logging
│   │   ├── schemas/             # Pydantic DTO
│   │   ├── models/              # ORM-модели (SQLAlchemy)
│   │   ├── repositories/        # доступ к данным (document, chat)
│   │   ├── services/            # llm, rag, document, chat
│   │   ├── agents/              # LangGraph: state, nodes, graph
│   │   ├── tools/               # search_documents
│   │   └── infrastructure/      # database, vectorstore, rabbitmq
│   ├── workers/document_worker.py
│   ├── tests/                   # pytest
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                    # Streamlit (chat + pages: документы, история)
├── sample_docs/                 # тестовый документ
├── docker-compose.yml
├── .env.example
└── README.md
```

## Тесты

Юнит-тесты на чистую логику (парсинг, чанкинг, построение RAG-промпта,
маршрутизация агента) — без обращения к Ollama/БД/Chroma:

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Roadmap (production-улучшения)

- Alembic-миграции вместо `create_all`
- Фильтрация retrieval по `document_id` (выбор документа в UI)
- Роли пользователей и аутентификация
- Dead-letter очередь и ретраи для worker
- Helm chart, Kubernetes manifests, Jenkinsfile, ArgoCD

---

## Запуск этапа 1 (локально, без Docker)

### Предусловия

Ollama запущена, модели стянуты:

```bash
ollama list
# qwen3:14b              — чат-модель
# nomic-embed-text       — embeddings (нужна на этапе 3)
```

### Шаги

```bash
# 1. Из корня проекта скопировать конфиг
cp .env.example .env

# 2. Виртуальное окружение и зависимости
cd backend
python -m venv .venv\Scripts\activate
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt

# 3. Запуск (из папки backend/)
uvicorn app.main:app --reload --port 8000
```

> `.env` лежит в корне проекта, а сервер запускается из `backend/`.
> pydantic-settings ищет `.env` в текущей рабочей директории, поэтому запускай
> uvicorn из корня **или** скопируй `.env` в `backend/`. Проще — скопировать:
> `cp .env backend/.env`.

### Проверка

Swagger UI: открой http://localhost:8000/docs

```bash
# health
curl http://localhost:8000/health
# → {"status":"ok","app":"Corporate AI Assistant","model":"qwen3:14b"}

# chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Привет! Ответь одним предложением, кто ты."}'
# → {"answer":"...","model":"qwen3:14b"}
```

Первый запрос к `qwen3:14b` может занять 10–30 сек (модель грузится в память).

---

## Запуск этапа 2 (Streamlit UI)

Нужно **два** запущенных процесса: backend (как выше) и frontend.

```bash
# Терминал 1 — backend (если ещё не запущен)
cd backend && uvicorn app.main:app --reload --port 8000

# Терминал 2 — frontend
cd frontend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Откроется http://localhost:8501. В сайдбаре — индикатор статуса backend.
Введи вопрос в поле внизу → ответ появится в чате.

> `api_client.py` читает адрес backend из переменной `BACKEND_URL`
> (по умолчанию `http://localhost:8000`). Streamlit ходит к FastAPI
> server-side, поэтому CORS для этой связки не обязателен — он добавлен в
> backend на будущее (прямые запросы из браузера).

---

## Запуск этапа 3 (RAG)

Стяни модель эмбеддингов и переустанови зависимости backend:

```bash
ollama pull nomic-embed-text
cd backend && pip install -r requirements.txt
```

Перезапусти сервисы. Загрузка документов — на странице «📄 Документы».
Chroma создаст папку `backend/chroma_data/` (в .gitignore). nomic-embed-text
кодируется с префиксами `search_query:` / `search_document:` — при смене этой
логики базу нужно переиндексировать (удалить `chroma_data` и перезалить файлы).

Очистка базы знаний (останови backend, иначе файл занят):

```powershell
Remove-Item -Recurse -Force backend\chroma_data
```

---

## Запуск этапа 4 (LangGraph-агент)

Добавилась зависимость `langgraph`:

```bash
cd backend && pip install -r requirements.txt
```

### Граф агента

```
START → router ──(search)──→ retrieve → generate → END
               └─(direct)──→ direct ─────────────→ END
```

- **router** — LLM-классификатор: нужен ли поиск по базе (SEARCH / DIRECT).
- **retrieve** — вызывает tool `search_documents` (поиск по Chroma).
- **generate** — отвечает строго по найденному контексту (RAG).
- **direct** — отвечает без базы (приветствие, общий вопрос).

Проверка: вопрос по документу → маршрут «поиск» + источники; приветствие →
маршрут «прямой ответ». Под каждым ответом в чате виден выбранный маршрут (🧭).

---

## Запуск этапа 5 (PostgreSQL)

### 1. Поднять Postgres в Docker (один раз)

```powershell
docker run --name corpai-postgres ^
  -e POSTGRES_USER=corpai -e POSTGRES_PASSWORD=corpai -e POSTGRES_DB=corpai ^
  -p 5432:5432 -d postgres:16
```

`docker ps` — проверить, что контейнер `corpai-postgres` запущен.
Если остановлен после перезагрузки: `docker start corpai-postgres`.

### 2. Зависимости и запуск

```bash
cd backend && pip install -r requirements.txt   # добавились sqlalchemy, psycopg2-binary
python -m uvicorn app.main:app --reload --port 8000
```

Таблицы (`documents`, `sessions`, `messages`, `sources`) создаются автоматически
при старте backend (`create_all`). В проде эту роль возьмёт Alembic — см. roadmap.

### Новые эндпоинты

- `GET /sessions` — список бесед.
- `GET /sessions/{id}` — беседа с сообщениями, источниками, оценками.
- `POST /chat/feedback` — оценка ответа (`{message_id, rating}`, rating = 1 / -1).
- `POST /chat` — теперь принимает `session_id` и возвращает `session_id` + `message_id`.

### Проверка

1. Задай вопрос → под ответом появятся кнопки 👍/👎, оценка сохранится в БД.
2. Открой страницу «🕓 История» → выбери беседу → увидишь сообщения, источники, оценку.
3. Перезапусти backend → история на странице «🕓 История» сохранится (это и есть persistence).

Заглянуть в БД напрямую:

```powershell
docker exec -it corpai-postgres psql -U corpai -d corpai -c "SELECT role, left(content,40), rating FROM messages ORDER BY created_at DESC LIMIT 10;"
```

---

## Запуск этапа 6 (RabbitMQ + worker, Chroma server)

Обработка документов теперь асинхронная. Chroma переехала в server-режим, чтобы
backend и worker писали/читали одну базу.

### 1. Поднять брокер и Chroma в Docker

```powershell
# RabbitMQ (с веб-консолью на http://localhost:15672, guest/guest)
docker run -d --name corpai-rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

# Chroma server. ВАЖНО: тег образа должен совпадать с версией python-клиента,
# иначе client/server могут быть несовместимы. Узнай версию:
#   pip show chromadb   → Version: X.Y.Z
# и подставь её в тег:
docker run -d --name corpai-chroma -p 8001:8000 chromadb/chroma:X.Y.Z
```

`docker ps` — должны работать `corpai-postgres`, `corpai-rabbitmq`, `corpai-chroma`.

### 2. Установить зависимости и запустить три процесса

```bash
cd backend && pip install -r requirements.txt   # добавился pika

# Терминал A — backend
python -m uvicorn app.main:app --reload --port 8000

# Терминал B — worker (тот же venv, из папки backend)
python -m workers.document_worker

# Терминал C — frontend
cd ../frontend && python -m streamlit run streamlit_app.py
```

> Chroma переехала с embedded на server — старые векторы из `chroma_data/` туда
> не переносятся. Перезалей документы через UI.

### Поток обработки

```
upload → файл в UPLOAD_DIR + запись (pending) → RabbitMQ (document_processing)
       → worker: extract → chunk → embed → Chroma → статус processed/failed
```

### Проверка

1. Загрузи документ → статус **⏳ pending**, ответ мгновенный (202 Accepted).
2. В терминале B видно, как worker берёт задачу и пишет «Готово (N чанков)».
3. Нажми «🔄 Обновить» на странице Документы → статус **✅ processed**.
4. Задай вопрос → backend находит чанки, добавленные worker'ом (общая Chroma).
5. Очередь и сообщения видно в консоли RabbitMQ: http://localhost:15672.

Останови worker (терминал B) и загрузи файл — он повиснет в **pending**, пока
worker снова не запустится и не разберёт очередь. Это и есть развязка через очередь.

---

## Запуск этапа 7 (Docker Compose) — весь стек одной командой

`docker-compose up` поднимает 6 сервисов: `backend`, `worker`, `frontend`,
`db` (postgres), `rabbitmq`, `chroma`. **Ollama остаётся на хосте** — контейнеры
ходят к ней через `host.docker.internal`.

### Подготовка

1. **Останови standalone-контейнеры из этапов 5–6**, иначе конфликт портов/имён:

   ```powershell
   docker rm -f corpai-postgres corpai-rabbitmq corpai-chroma
   ```

   Данные в них не переносятся в compose (тома отдельные) — документы перезальёшь.

2. **Пропиши `CHROMA_VERSION` в корневом `.env`** — это твоя версия клиента
   (`pip show chromadb`). Один и тот же номер идёт и в образ сервера chroma, и в
   пин клиента внутри образа backend:

   ```
   CHROMA_VERSION=0.5.23
   ```

3. Убедись, что Ollama запущена на хосте и модели стянуты (`ollama list`).

### Запуск

```powershell
docker-compose up --build
```

Первая сборка идёт несколько минут (ставятся зависимости, тянутся образы).
Останов: `Ctrl+C`, полностью убрать с томами: `docker-compose down -v`.

| Сервис    | Адрес                       |
|-----------|-----------------------------|
| Frontend  | http://localhost:8501       |
| Backend   | http://localhost:8000/docs  |
| RabbitMQ  | http://localhost:15672 (guest/guest) |

### Как устроена сеть

- Внутри compose сервисы видят друг друга по имени: `db:5432`, `rabbitmq:5672`,
  `chroma:8000`. Эти адреса заданы в `docker-compose.yml` (блок `x-backend-env`)
  и переопределяют `localhost`-дефолты из `.env`.
- `backend` и `worker` — **один образ** (`corpai-backend`), отличаются только
  командой запуска.
- `backend` и `worker` делят том `uploads` — worker читает файлы, сохранённые
  backend'ом.
- `depends_on` + healthcheck'и гарантируют порядок: backend стартует после
  готовности postgres, worker — после rabbitmq.

### Проверка

1. Открой http://localhost:8501 → загрузи документ → дождись `processed`.
2. Задай вопрос → ответ с источниками.
3. `docker-compose ps` — все сервисы `Up`.
4. `docker-compose logs -f worker` — видно обработку задач.
