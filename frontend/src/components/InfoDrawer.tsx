import { useEffect } from "react";
import { GLOSSARY } from "../lib/glossary";

interface Props {
  topic: string | null;
  onClose: () => void;
}

export default function InfoDrawer({ topic, onClose }: Props) {
  useEffect(() => {
    if (!topic) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [topic, onClose]);

  if (!topic) return null;

  const entry = GLOSSARY[topic];
  if (!entry) return null;

  return (
    <div className="info-drawer-overlay" onClick={onClose}>
      <div
        className="info-drawer"
        role="dialog"
        aria-modal="true"
        aria-label={entry.title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="info-drawer-header">
          <h3>{entry.title}</h3>
          <button type="button" className="info-drawer-close" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </div>
        <div className="info-drawer-body">
          {entry.body.map((paragraph, i) => (
            <p key={i} className={i === entry.body.length - 1 ? "info-drawer-note" : undefined}>
              {paragraph}
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
