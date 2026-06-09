"""HTTP-клиент к FastAPI backend."""

import os

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CHAT_TIMEOUT = int(os.getenv("CHAT_TIMEOUT", "180"))


class BackendError(Exception):
    """Проблема общения с backend (показывается пользователю)."""


def _detail(resp: requests.Response) -> str:
    try:
        return resp.json().get("detail", resp.text)
    except ValueError:
        return resp.text


def send_chat(
    message: str,
    session_id: str | None = None,
    system_prompt: str | None = None,
) -> dict:
    payload: dict = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    if system_prompt:
        payload["system_prompt"] = system_prompt

    try:
        resp = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=CHAT_TIMEOUT)
    except requests.ConnectionError as exc:
        raise BackendError(f"Backend недоступен по адресу {BACKEND_URL}.") from exc
    except requests.Timeout as exc:
        raise BackendError("Backend не ответил вовремя.") from exc

    if resp.status_code != 200:
        raise BackendError(f"Ошибка backend ({resp.status_code}): {_detail(resp)}")
    return resp.json()


def upload_document(filename: str, file_bytes: bytes) -> dict:
    try:
        resp = requests.post(
            f"{BACKEND_URL}/documents/upload",
            files={"file": (filename, file_bytes)},
            timeout=CHAT_TIMEOUT,
        )
    except requests.ConnectionError as exc:
        raise BackendError(f"Backend недоступен по адресу {BACKEND_URL}.") from exc
    except requests.Timeout as exc:
        raise BackendError("Загрузка заняла слишком долго (таймаут).") from exc

    if resp.status_code not in (200, 202):
        raise BackendError(f"Ошибка загрузки ({resp.status_code}): {_detail(resp)}")
    return resp.json()


def list_documents() -> list[dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/documents", timeout=10)
    except requests.RequestException as exc:
        raise BackendError(f"Backend недоступен по адресу {BACKEND_URL}.") from exc
    if resp.status_code != 200:
        raise BackendError(f"Ошибка получения списка ({resp.status_code})")
    return resp.json()


def send_feedback(message_id: str, rating: int) -> None:
    try:
        resp = requests.post(
            f"{BACKEND_URL}/chat/feedback",
            json={"message_id": message_id, "rating": rating},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise BackendError(f"Backend недоступен по адресу {BACKEND_URL}.") from exc
    if resp.status_code != 200:
        raise BackendError(f"Не удалось сохранить оценку ({resp.status_code})")


def list_sessions() -> list[dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/sessions", timeout=10)
    except requests.RequestException as exc:
        raise BackendError(f"Backend недоступен по адресу {BACKEND_URL}.") from exc
    if resp.status_code != 200:
        raise BackendError(f"Ошибка получения сессий ({resp.status_code})")
    return resp.json()


def get_session(session_id: str) -> dict:
    try:
        resp = requests.get(f"{BACKEND_URL}/sessions/{session_id}", timeout=10)
    except requests.RequestException as exc:
        raise BackendError(f"Backend недоступен по адресу {BACKEND_URL}.") from exc
    if resp.status_code != 200:
        raise BackendError(f"Ошибка получения сессии ({resp.status_code})")
    return resp.json()


def check_health() -> dict | None:
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        return None
    return None
