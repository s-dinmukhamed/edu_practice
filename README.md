---
title: YOLO Detector API
emoji: 🔍
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
---

# YOLO Detector API

FastAPI backend for YOLO image classification/detection.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Статус сервиса и модели |
| POST | `/detect` | Детекция объектов на изображении |
| GET | `/classes` | Список всех классов модели |

## Deploy

1. Загрузи `best.pt` в корень Space
2. Space автоматически запустит Docker-контейнер

## Local dev

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```
