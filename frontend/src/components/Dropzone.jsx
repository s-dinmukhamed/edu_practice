import { useCallback } from "react";

export default function Dropzone({ onFiles }) {
  const handleDrop = useCallback(
    (e) => {
      e.preventDefault();
      const arr = Array.from(e.dataTransfer.files).filter((f) =>
        f.type.startsWith("image/")
      );
      if (arr.length) onFiles(arr);
    },
    [onFiles]
  );

  return (
    <div
      className="dropzone"
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      <div className="dropzone-icon">🖼️</div>
      <p className="dropzone-title">Перетащи изображения сюда</p>
      <p className="dropzone-hint">или воспользуйся кнопками слева</p>
      <p className="dropzone-formats">JPG · PNG · WebP · BMP</p>
    </div>
  );
}
