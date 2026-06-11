from __future__ import annotations
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

_COLORS = [
    (255, 56, 56), (255, 157, 151), (255, 112, 31), (255, 178, 29),
    (207, 210, 49), (72, 249, 10), (146, 204, 23), (61, 219, 134),
    (26, 147, 52), (0, 212, 187), (44, 153, 168), (0, 194, 255),
    (52, 69, 147), (100, 115, 255), (0, 24, 236), (132, 56, 255),
    (82, 0, 133), (203, 56, 255), (255, 149, 200), (255, 55, 199),
]


class YOLODetector:
    def __init__(self, model_path: str = "best.pt"):
        self._model = YOLO(model_path)

    # ── Публичные методы ───────────────────────────────────────────────────────

    def detect(self, image_path: str, conf: float = 0.25) -> tuple[Image.Image, list[dict]]:
        """Детекция по пути к файлу (для обратной совместимости)."""
        img = cv2.imread(image_path)
        if img is None:
            pil = Image.open(image_path).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        return self.detect_from_array(img, conf=conf)

    def detect_from_array(self, img_bgr: np.ndarray, conf: float = 0.25) -> tuple[Image.Image, list[dict]]:
        """
        Детекция из BGR numpy-массива.
        Используется в FastAPI — не требует записи на диск.
        Возвращает (аннотированный PIL Image, список детекций).
        """
        results = self._model(img_bgr, imgsz=640, conf=conf, verbose=False)[0]
        annotated = img_bgr.copy()
        detections: list[dict] = []

        # Классификатор — probs есть, boxes нет
        if results.probs is not None:
            top1_id = int(results.probs.top1)
            top1_conf = float(results.probs.top1conf)
            label = results.names[top1_id]
            color = _COLORS[top1_id % len(_COLORS)]
            h, w = img_bgr.shape[:2]

            frame_color = color if top1_conf >= conf else (120, 120, 120)
            cv2.rectangle(annotated, (0, 0), (w - 1, h - 1), frame_color, 4)

            text = f"{label}  {top1_conf:.1%}"
            font_scale = max(0.8, min(w / 400, 2.0))
            thickness = max(2, int(font_scale * 2))
            (tw, th), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )
            pad = 10
            cv2.rectangle(annotated, (0, 0), (tw + pad * 2, th + baseline + pad * 2),
                          frame_color, -1)
            cv2.putText(annotated, text, (pad, th + pad),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                        (255, 255, 255), thickness, cv2.LINE_AA)

            if top1_conf < conf:
                warn = "low confidence"
                cv2.putText(annotated, warn, (pad, th + pad * 3 + th),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (80, 80, 255), 1, cv2.LINE_AA)

            detections.append({"label": label, "confidence": top1_conf, "box": [0, 0, w, h]})

        # Детектор — boxes
        elif results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                label = results.names[cls_id]
                confidence = float(box.conf[0])
                if confidence < conf:
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                color = _COLORS[cls_id % len(_COLORS)]

                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                text = f"{label} {confidence:.0%}"
                (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                bar_y = max(y1 - th - 8, 0)
                cv2.rectangle(annotated, (x1, bar_y), (x1 + tw + 8, y1), color, -1)
                cv2.putText(annotated, text, (x1 + 4, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

                detections.append({"label": label, "confidence": confidence, "box": [x1, y1, x2, y2]})

        rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb), detections
