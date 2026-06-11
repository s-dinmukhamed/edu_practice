import { useState, useCallback, useRef, useEffect } from "react";
import Dropzone from "./components/Dropzone";
import ImageViewer from "./components/ImageViewer";
import Sidebar from "./components/Sidebar";
import ResultsPanel from "./components/ResultsPanel";
import StatusBar from "./components/StatusBar";
import { detectImage } from "./api";

export default function App() {
  const [files, setFiles] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [conf, setConf] = useState(0.25);
  const [modelStatus, setModelStatus] = useState({ loaded: false, error: null, classes: null });
  const [result, setResult] = useState(null); // { annotated, detections, ms }
  const [status, setStatus] = useState("Проверка модели…");
  const [isDetecting, setIsDetecting] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);

  const API_URL = import.meta.env.VITE_API_URL || "https://fu4ll-back-practice.hf.space/";

  // ── Проверка модели при загрузке ──────────────────────────────────────────

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then((d) => {
        setModelStatus({ loaded: d.model_loaded, error: d.model_error, classes: d.classes_count });
        setStatus(
          d.model_loaded
            ? `Модель загружена ✓  (${d.classes_count} классов)`
            : `Ошибка модели: ${d.model_error}`
        );
      })
      .catch(() => setStatus("Не удалось подключиться к серверу"));
  }, [API_URL]);

  // ── Загрузка файлов ───────────────────────────────────────────────────────

  const handleFiles = useCallback((newFiles) => {
    setFiles(newFiles);
    setCurrentIndex(0);
    setResult(null);
    const url = URL.createObjectURL(newFiles[0]);
    setPreviewUrl(url);
    setStatus(`Загружено ${newFiles.length} файл(ов)`);
  }, []);

  const handleSelect = useCallback(
    (index) => {
      setCurrentIndex(index);
      setResult(null);
      const url = URL.createObjectURL(files[index]);
      setPreviewUrl(url);
    },
    [files]
  );

  // ── Детекция ──────────────────────────────────────────────────────────────

  const handleDetect = useCallback(async () => {
    if (!files.length) return;
    setIsDetecting(true);
    setStatus("Детекция…");
    try {
      const data = await detectImage(API_URL, files[currentIndex], conf);
      setResult(data);
      setStatus(
        `${files[currentIndex].name} — найдено: ${data.detections.length} | ${data.inference_ms} мс`
      );
    } catch (e) {
      setStatus(`Ошибка: ${e.message}`);
    } finally {
      setIsDetecting(false);
    }
  }, [API_URL, files, currentIndex, conf]);

  // ── Скачать аннотированное изображение ────────────────────────────────────

  const handleSave = useCallback(() => {
    if (!result?.annotated_image) return;
    const a = document.createElement("a");
    a.href = `data:image/jpeg;base64,${result.annotated_image}`;
    a.download = `detected_${files[currentIndex]?.name || "result.jpg"}`;
    a.click();
  }, [result, files, currentIndex]);

  const displaySrc = result
    ? `data:image/jpeg;base64,${result.annotated_image}`
    : previewUrl;

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <span className="header-icon">🔍</span>
          <span className="header-title">YOLO Detector</span>
        </div>
        <div className={`model-badge ${modelStatus.loaded ? "ok" : "err"}`}>
          {modelStatus.loaded ? "Модель готова" : "Модель недоступна"}
        </div>
      </header>

      <div className="layout">
        {/* Левая панель: список файлов + настройки */}
        <Sidebar
          files={files}
          currentIndex={currentIndex}
          conf={conf}
          onConfChange={setConf}
          onSelect={handleSelect}
          onOpenFiles={handleFiles}
          onDetect={handleDetect}
          onSave={handleSave}
          isDetecting={isDetecting}
          hasResult={!!result}
          modelLoaded={modelStatus.loaded}
        />

        {/* Центр: изображение */}
        <main className="center">
          {displaySrc ? (
            <ImageViewer src={displaySrc} />
          ) : (
            <Dropzone onFiles={handleFiles} />
          )}
        </main>

        {/* Правая панель: результаты */}
        <ResultsPanel detections={result?.detections || null} isDetecting={isDetecting} />
      </div>

      <StatusBar text={status} isDetecting={isDetecting} />
    </div>
  );
}
