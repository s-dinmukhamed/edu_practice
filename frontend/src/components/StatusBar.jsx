export default function StatusBar({ text, isDetecting }) {
  return (
    <footer className="status-bar">
      <span className="status-text">{text}</span>
      {isDetecting && <span className="status-spinner" />}
    </footer>
  );
}
