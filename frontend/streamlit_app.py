"""Streamlit UI — экран чата с историей, источниками и оценками."""

import streamlit as st

from api_client import (
    BackendError,
    check_health,
    get_session,
    list_sessions,
    send_chat,
    send_feedback,
)

st.set_page_config(page_title="Corporate AI Assistant", page_icon="🤖")


def load_session(session_id: str) -> None:
    """Загрузить беседу из БД в состояние, чтобы продолжить её."""
    data = get_session(session_id)
    messages = []
    for m in data["messages"]:
        entry = {"role": m["role"], "content": m["content"]}
        if m["role"] == "assistant":
            entry["sources"] = m.get("sources", [])
            entry["route"] = m.get("route", "")
            entry["message_id"] = m["id"]
            if m.get("rating") in (1, -1):
                st.session_state.setdefault("rated", {})[m["id"]] = m["rating"]
        messages.append(entry)
    st.session_state.messages = messages
    st.session_state.session_id = session_id


# ── Сайдбар ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Статус")
    health = check_health()
    if health:
        st.success(f"Backend online · модель {health.get('model', '?')}")
    else:
        st.error("Backend offline — запусти uvicorn")

    st.divider()
    system_prompt = st.text_area(
        "Системный промпт (необязательно)",
        value="Ты — корпоративный ассистент. Отвечай кратко и по делу.",
        height=100,
    )
    if st.button("🆕 Новая беседа", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    st.divider()
    st.subheader("🕓 Недавние")
    current_id = st.session_state.get("session_id")
    try:
        recent = list_sessions()
    except BackendError:
        recent = []
    if not recent:
        st.caption("Пока нет бесед.")
    for s in recent[:20]:
        prefix = "✅ " if s["id"] == current_id else ""
        title = s.get("title") or "Без названия"
        if st.button(f"{prefix}{title}", key=f"sess_{s['id']}", use_container_width=True):
            load_session(s["id"])
            st.rerun()

# ── Состояние ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "rated" not in st.session_state:
    st.session_state.rated = {}

st.title("🤖 Corporate AI Assistant")
st.caption("RAG + LangGraph-агент с историей в PostgreSQL.")


def render_route(route: str) -> None:
    if route == "direct":
        st.caption("🧭 Маршрут агента: прямой ответ (без поиска по базе)")
    elif route == "search":
        st.caption("🧭 Маршрут агента: поиск по базе знаний")


def render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(f"📎 Источники ({len(sources)})"):
        for i, src in enumerate(sources, start=1):
            st.markdown(
                f"**[{i}] {src['filename']}** · чанк #{src['chunk_index']} · "
                f"дистанция {src['score']:.3f}"
            )
            st.caption(src["snippet"])


def render_feedback(message_id: str) -> None:
    if not message_id:
        return
    rated = st.session_state.rated
    if message_id in rated:
        st.caption("Оценка: " + ("👍" if rated[message_id] == 1 else "👎"))
        return

    col_up, col_down, _ = st.columns([1, 1, 8])
    clicked = 1 if col_up.button("👍", key=f"up_{message_id}") else None
    if col_down.button("👎", key=f"down_{message_id}"):
        clicked = -1
    if clicked is not None:
        try:
            send_feedback(message_id, clicked)
            st.session_state.rated[message_id] = clicked
            st.toast("Спасибо за оценку!")
        except BackendError as exc:
            st.toast(f"⚠️ {exc}")
        st.rerun()


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_route(msg.get("route", ""))
            render_sources(msg.get("sources", []))
            render_feedback(msg.get("message_id", ""))

# ── Ввод ───────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Задай вопрос по документам..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        sources: list[dict] = []
        route = ""
        message_id = ""
        with st.spinner("Агент думает: выбираю маршрут и формирую ответ..."):
            try:
                result = send_chat(
                    prompt,
                    session_id=st.session_state.session_id,
                    system_prompt=system_prompt or None,
                )
                answer = result["answer"]
                sources = result.get("sources", [])
                route = result.get("route", "")
                message_id = result.get("message_id", "")
                st.session_state.session_id = result.get("session_id")
            except BackendError as exc:
                answer = f"⚠️ {exc}"
        st.markdown(answer)
        render_route(route)
        render_sources(sources)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "route": route,
            "message_id": message_id,
        }
    )
    st.rerun()
