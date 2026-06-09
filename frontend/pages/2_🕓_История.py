"""Страница История — читает беседы из PostgreSQL через backend.

В отличие от экрана чата (память браузерной сессии), здесь данные берутся из БД,
поэтому история переживает перезапуск и видна целиком.
"""

import streamlit as st

from api_client import BackendError, get_session, list_sessions

st.set_page_config(page_title="История", page_icon="🕓")
st.title("🕓 История бесед")
st.caption("Сохранённые сессии, сообщения, источники и оценки из PostgreSQL.")

try:
    sessions = list_sessions()
except BackendError as exc:
    st.error(f"⚠️ {exc}")
    st.stop()

if not sessions:
    st.info("Пока нет сохранённых бесед. Задай вопрос на экране чата.")
    st.stop()

# Выбор сессии
options = {
    f"{s['created_at'][:19]} · {s['message_count']} сообщ. · {s['id'][:8]}…": s["id"]
    for s in sessions
}
label = st.selectbox("Выбери беседу", list(options.keys()))
session_id = options[label]

try:
    data = get_session(session_id)
except BackendError as exc:
    st.error(f"⚠️ {exc}")
    st.stop()

st.divider()
for msg in data["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("route"):
                st.caption(f"🧭 Маршрут: {msg['route']}")
            rating = msg.get("rating")
            if rating == 1:
                st.caption("Оценка: 👍")
            elif rating == -1:
                st.caption("Оценка: 👎")
            sources = msg.get("sources", [])
            if sources:
                with st.expander(f"📎 Источники ({len(sources)})"):
                    for i, src in enumerate(sources, start=1):
                        st.markdown(
                            f"**[{i}] {src['filename']}** · чанк #{src['chunk_index']} "
                            f"· дистанция {src['score']:.3f}"
                        )
                        st.caption(src["snippet"])
