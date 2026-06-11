import { useRef } from "react";

export default function Sidebar({
  files, currentIndex, conf, onConfChange,
  onSelect, onOpenFiles, onDetect, onSave,
  isDetecting, hasResult, modelLoaded,
}) {
  const fileInputRef = useRef();
  const folderInputRef = useRef();

  const handleFileInput = (e) => {
    const arr = Array.from(e.target.files).filter(isImage);
    if (arr.length) onOpenFiles(arr);
    e.target.value = "";
  };

  return (
    <aside className="sidebar">
      {/* Открыть файлы */}
      <div className="sidebar-section">
        <button className="btn" onClick={() => fileInputRef.current.click()}>
          Открыть файл
        </button>
        <button className="btn" onClick={() => folderInputRef.current.click()}>
          Открыть папку
        </button>
        <input ref={fileInputRef} type="file" accept="image/*" multiple hidden onChange={handleFileInput} />
        <input ref={folderInputRef} type="file" accept="image/*" multiple hidden
          // @ts-ignore
          webkitdirectory="" onChange={handleFileInput} />
      </div>

      {/* Список файлов */}
      {files.length > 0 && (
        <div className="sidebar-section sidebar-files">
          <p className="sidebar-label">Файлы ({files.length})</p>
          <ul className="file-list">
            {files.map((f, i) => (
              <li
                key={f.name + i}
                className={`file-item ${i === currentIndex ? "active" : ""}`}
                onClick={() => onSelect(i)}
              >
                {f.name}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Порог уверенности */}
      <div className="sidebar-section">
        <label className="sidebar-label">
          Порог уверенности — <strong>{conf.toFixed(2)}</strong>
        </label>
        <input
          type="range" min="0.01" max="0.99" step="0.01"
          value={conf}
          onChange={(e) => onConfChange(parseFloat(e.target.value))}
          className="slider"
        />
        <div className="slider-hints">
          <span>0.01</span><span>0.50</span><span>0.99</span>
        </div>
      </div>

      {/* Действия */}
      <div className="sidebar-section sidebar-actions">
        <button
          className="btn btn-primary"
          onClick={onDetect}
          disabled={!files.length || !modelLoaded || isDetecting}
        >
          {isDetecting ? "Анализ…" : "Запустить детекцию"}
        </button>
        {hasResult && (
          <button className="btn" onClick={onSave}>
            Сохранить результат
          </button>
        )}
      </div>
    </aside>
  );
}

function isImage(f) {
  return f.type.startsWith("image/");
}
