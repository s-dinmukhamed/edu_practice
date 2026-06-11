export default function ImageViewer({ src }) {
  return (
    <div className="image-viewer">
      <img src={src} alt="Просмотр" className="viewer-img" />
    </div>
  );
}
