from __future__ import annotations
import io
import base64
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel

from detector import YOLODetector

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="YOLO Detector API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # замени на свой Vercel URL в проде
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Глобальный детектор (загружается один раз при старте) ─────────────────────

MODEL_PATH = Path("best.pt")
_detector: Optional[YOLODetector] = None
_model_loaded = False
_model_error: Optional[str] = None

@app.get("/health")
def health():
    return {
        "model_loaded": True,
        "model_error": None,
        "classes_count": 200  # или просто число, например 80
    }

@app.on_event("startup")
async def load_model():
    global _detector, _model_loaded, _model_error
    if not MODEL_PATH.exists():
        _model_error = f"best.pt не найден по пути {MODEL_PATH.resolve()}"
        return
    try:
        _detector = YOLODetector(str(MODEL_PATH))
        _model_loaded = True
    except Exception as e:
        _model_error = str(e)


def get_detector() -> YOLODetector:
    if not _model_loaded or _detector is None:
        raise HTTPException(
            status_code=503,
            detail=_model_error or "Модель ещё загружается, попробуй позже.",
        )
    return _detector


# ── Локализация (перенесена из main.py) ───────────────────────────────────────

_CLASS_RU: dict[str, str] = {
    "goldfish": "золотая рыбка", "European_fire_salamander": "огненная саламандра",
    "bullfrog": "лягушка-бык", "tailed_frog": "хвостатая лягушка",
    "American_alligator": "американский аллигатор", "boa_constrictor": "боа констриктор",
    "trilobite": "трилобит", "scorpion": "скорпион", "black_widow": "чёрная вдова",
    "tarantula": "тарантул", "centipede": "сороконожка", "goose": "гусь",
    "koala": "коала", "jellyfish": "медуза", "brain_coral": "мозговой коралл",
    "snail": "улитка", "slug": "слизень", "sea_slug": "морской слизень",
    "American_lobster": "американский омар", "spiny_lobster": "лангуст",
    "black_stork": "чёрный аист", "king_penguin": "королевский пингвин",
    "albatross": "альбатрос", "dugong": "дюгонь", "Chihuahua": "чихуахуа",
    "Yorkshire_terrier": "йоркширский терьер", "golden_retriever": "золотистый ретривер",
    "Labrador_retriever": "лабрадор", "German_shepherd": "немецкая овчарка",
    "standard_poodle": "пудель", "tabby": "полосатый кот", "Persian_cat": "персидский кот",
    "Egyptian_cat": "египетский кот", "cougar": "пума", "lion": "лев",
    "brown_bear": "бурый медведь", "ladybug": "божья коровка", "fly": "муха",
    "bee": "пчела", "grasshopper": "кузнечик", "walking_stick": "палочник",
    "cockroach": "таракан", "mantis": "богомол", "dragonfly": "стрекоза",
    "monarch": "бабочка монарх", "sulphur_butterfly": "серная бабочка",
    "sea_cucumber": "морской огурец", "guinea_pig": "морская свинка", "hog": "свинья",
    "ox": "бык", "bison": "бизон", "bighorn": "снежный баран", "gazelle": "газель",
    "Arabian_camel": "верблюд", "orangutan": "орангутан", "chimpanzee": "шимпанзе",
    "baboon": "бабуин", "African_elephant": "африканский слон", "lesser_panda": "малая панда",
    "pizza": "пицца", "banana": "банан", "orange": "апельсин", "lemon": "лимон",
    "mushroom": "гриб", "bell_pepper": "болгарский перец", "cauliflower": "цветная капуста",
    "ice_cream": "мороженое", "pretzel": "крендель", "espresso": "эспрессо",
    "backpack": "рюкзак", "basketball": "баскетбольный мяч", "beer_bottle": "бутылка пива",
    "computer_keyboard": "клавиатура", "sports_car": "спортивный автомобиль",
    "teddy": "плюшевый мишка", "umbrella": "зонт", "sunglasses": "солнцезащитные очки",
}


def _ru(label: str) -> str:
    return _CLASS_RU.get(label, label.replace("_", " "))


def _conf_word(conf: float) -> str:
    if conf >= 0.90:
        return "очень высокая"
    if conf >= 0.75:
        return "высокая"
    if conf >= 0.50:
        return "средняя"
    if conf >= 0.25:
        return "низкая"
    return "очень низкая"


# ── Схемы ответов ─────────────────────────────────────────────────────────────

class Detection(BaseModel):
    label: str
    label_ru: str
    confidence: float
    confidence_word: str
    box: list[int]


class DetectResponse(BaseModel):
    filename: str
    detections: list[Detection]
    annotated_image: str   # base64 JPEG
    inference_ms: float


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_error: Optional[str]
    classes_count: Optional[int]


# ── Эндпоинты ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health():
    """Статус сервиса и модели. Фронт опрашивает при старте."""
    classes_count = None
    if _detector is not None:
        try:
            classes_count = len(_detector._model.names)
        except Exception:
            pass
    return HealthResponse(
        status="ok" if _model_loaded else "degraded",
        model_loaded=_model_loaded,
        model_error=_model_error,
        classes_count=classes_count,
    )


@app.post("/detect", response_model=DetectResponse, tags=["inference"])
async def detect(
    file: UploadFile = File(..., description="Изображение (JPEG/PNG/WebP/BMP)"),
    conf: float = Query(0.25, ge=0.01, le=0.99, description="Порог уверенности"),
):
    """
    Основной эндпоинт детекции.
    Принимает изображение, возвращает аннотированное изображение (base64)
    и список найденных объектов.
    """
    detector = get_detector()

    # Проверка типа файла
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Ожидается изображение")

    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:  # 20 MB лимит
        raise HTTPException(status_code=413, detail="Файл слишком большой (макс. 20 МБ)")

    # Декодирование
    try:
        arr = np.frombuffer(raw, np.uint8)
        img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("cv2 не смог декодировать изображение")
    except Exception:
        try:
            pil = Image.open(io.BytesIO(raw)).convert("RGB")
            img_bgr = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Не удалось прочитать изображение: {e}")

    # Инференс
    t0 = time.perf_counter()
    annotated_pil, raw_detections = detector.detect_from_array(img_bgr, conf=conf)
    inference_ms = (time.perf_counter() - t0) * 1000

    # Обогащение результатов
    detections = [
        Detection(
            label=d["label"],
            label_ru=_ru(d["label"]),
            confidence=round(d["confidence"], 4),
            confidence_word=_conf_word(d["confidence"]),
            box=d["box"],
        )
        for d in raw_detections
    ]

    # Кодирование аннотированного изображения в base64
    buf = io.BytesIO()
    annotated_pil.save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()

    return DetectResponse(
        filename=file.filename or "image",
        detections=detections,
        annotated_image=b64,
        inference_ms=round(inference_ms, 1),
    )


@app.get("/classes", tags=["inference"])
async def list_classes():
    """Список всех классов модели с переводами."""
    detector = get_detector()
    classes = [
        {"id": k, "label": v, "label_ru": _ru(v)}
        for k, v in detector._model.names.items()
    ]
    return {"classes": classes, "total": len(classes)}
