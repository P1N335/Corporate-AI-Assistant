# Kubernetes-манифесты

Демонстрация деплоя проекта в кластер. Для локального запуска подойдёт
**kind** или **minikube**. Манифесты — в namespace `corpai`.

## Состав

| Файл | Что разворачивает |
|------|-------------------|
| `00-namespace.yaml` | namespace `corpai` |
| `01-config.yaml` | ConfigMap (несекретные настройки) |
| `02-secret.yaml` | Secret (пароли БД, URL'ы с креденшелами) |
| `10-postgres.yaml` | PostgreSQL (StatefulSet + Service + PVC) |
| `11-rabbitmq.yaml` | RabbitMQ (Deployment + Service + PVC) |
| `12-chroma.yaml` | Chroma server (Deployment + Service + PVC) |
| `20-backend.yaml` | FastAPI (Deployment x2 + Service) |
| `21-worker.yaml` | Document worker (Deployment) |
| `22-frontend.yaml` | Streamlit (Deployment + Service) |
| `23-ingress.yaml` | Ingress для UI (опционально) |
| `30-uploads-pvc.yaml` | общий том backend↔worker (RWX) |

## Перед деплоем

1. **Собрать и сделать образы доступными кластеру.** Образы `corpai-backend` и
   `corpai-frontend` локальные — их нужно загрузить в кластер или запушить в registry.

   ```bash
   docker build -t corpai-backend:latest ./backend
   docker build -t corpai-frontend:latest ./frontend
   # kind:
   kind load docker-image corpai-backend:latest corpai-frontend:latest
   # minikube:
   minikube image load corpai-backend:latest && minikube image load corpai-frontend:latest
   ```

2. **Указать адрес Ollama.** Ollama не в кластере. В `01-config.yaml` заменить
   `OLLAMA_HOST` на реальный адрес: внешний OpenAI-совместимый эндпоинт или
   IP хоста, доступный из подов.

3. **Сверить версию Chroma.** Тег образа в `12-chroma.yaml` должен совпадать с
   версией клиента chromadb в образе backend (см. `CHROMA_VERSION`).

4. **RWX-том.** `uploads` требует ReadWriteMany. Дефолтный StorageClass в
   kind/minikube даёт только RWO — для демо держи backend и worker на одной ноде
   или подключи RWX-провайдер (NFS и т.п.).

## Деплой

```bash
kubectl apply -f k8s/
kubectl -n corpai get pods -w     
```


```bash
kubectl -n corpai port-forward svc/frontend 8501:8501
# → http://localhost:8501
```

## Масштабирование и проверка

```bash
kubectl -n corpai scale deployment/worker --replicas=3   
kubectl -n corpai get pods
kubectl -n corpai logs deploy/worker -f
```

