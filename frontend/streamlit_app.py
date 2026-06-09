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
i