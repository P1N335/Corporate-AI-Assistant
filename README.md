# Corporate AI Assistant (RAG + Agents)

AI-агент для работы с внутренней базой знаний компании: пользователь загружает
документы, задаёт вопросы, агент ищет релевантный контекст через RAG, отвечает с
опорой на источники, при необходимости вызывает инструменты и сохраняет историю.


## Стек

Backend: Python 3.11+, FastAPI, Pydantic. LLM/Agents: LangChain, LangGraph,
Ollama (OpenAI-совместимый API). RAG: Chroma, nomic-embed-text. Хранилище:
PostgreSQL. Очереди: RabbitMQ. UI: Streamlit. DevOps: Docker Compose.

## Архитектура


![alt text](image.png)


Поток вопроса: UI → FastAPI → LangGraph-агент (router решает search/direct) →
tool `search_documents` → Chroma → LLM генерирует ответ по контексту → ответ с
источниками + запись хода в PostgreSQL.

Поток загрузки: UI → FastAPI сохраняет файл и ставит задачу в RabbitMQ → Worker
извлекает текст, чанкует, считает эмбеддинги и пишет в Chroma → статус документа
обновляется в PostgreSQL.


## Структура проекта


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


## Roadmap (production-улучшения)

- Alembic-миграции вместо `create_all`
- Фильтрация retrieval по `document_id` (выбор документа в UI)
- Роли пользователей и аутентификация
- Dead-letter очередь и ретраи для worker
- Helm chart, Kubernetes manifests, Jenkinsfile, ArgoCD