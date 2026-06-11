const CONF_COLOR = (c) => {
  if (c >= 0.9) return "conf-very-high";
  if (c >= 0.75) return "conf-high";
  if (c >= 0.5) return "conf-medium";
  if (c >= 0.25) return "conf-low";
  return "conf-very-low";
};

export default function ResultsPanel({ detections, isDetecting }) {
  return (
    <aside className="results-panel">
      <p className="sidebar-label">Объекты</p>

      {isDetecting && (
        <div className="results-placeholder">
          <div className="spinner" />
          <p>Анализирую…</p>
        </div>
      )}

      {!isDetecting && detections === null && (
        <p className="results-empty">Запусти детекцию, чтобы увидеть результаты</p>
      )}

      {!isDetecting && detections?.length === 0 && (
        <p className="results-empty">
          Объектов не обнаружено.<br />
          Попробуй снизить порог уверенности.
        </p>
      )}

      {!isDetecting && detections && detections.length > 0 && (
        <>
          {/* Лучший результат */}
          <div className="best-result">
            <p className="best-label-ru">{detections[0].label_ru}</p>
            <p className="best-label-en">{detections[0].label}</p>
            <div className={`conf-bar-wrap ${CONF_COLOR(detections[0].confidence)}`}>
              <div
                className="conf-bar-fill"
                style={{ width: `${detections[0].confidence * 100}%` }}
              />
            </div>
            <p className="conf-text">
              {(detections[0].confidence * 100).toFixed(1)}%
              &nbsp;—&nbsp;{detections[0].confidence_word}
            </p>
          </div>

          {/* Остальные (детектор) */}
          {detections.length > 1 && (
            <>
              <p className="sidebar-label" style={{ marginTop: "1rem" }}>
                Всего: {detections.length}
              </p>
              <ul className="det-list">
                {detections.map((d, i) => (
                  <li key={i} className="det-item">
                    <span className="det-name">{d.label_ru}</span>
                    <span className={`det-conf ${CONF_COLOR(d.confidence)}`}>
                      {(d.confidence * 100).toFixed(0)}%
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </aside>
  );
}
