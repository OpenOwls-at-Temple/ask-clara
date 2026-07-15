import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { saveBlob } from "../services/documents";

function ModalShell({ title, onClose, children, footer }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  // Portal to <body>: ancestors with CSS transforms (e.g. the page's fade-up
  // animation) would otherwise re-anchor position:fixed and misplace the
  // overlay away from the viewport.
  return createPortal(
    <div
      className="modal-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <div className="modal">
        <div className="modal-header">
          <div className="modal-title">{title}</div>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}

/** Shows the resume as plain text in a popup with a copy button. */
export function TextPreviewModal({ title, text, onClose }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <ModalShell
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>
            Close
          </button>
          <button className="btn btn-primary btn-sm" onClick={handleCopy}>
            {copied ? "✓ Copied!" : "Copy text"}
          </button>
        </>
      }
    >
      <pre className="modal-text">{text}</pre>
    </ModalShell>
  );
}

/**
 * Inline (non-popup) resume preview. Shows a server-rendered PNG of the
 * one-page resume as a plain image — no browser PDF-viewer chrome — and
 * fetches the actual PDF only when the student clicks download.
 */
export function ResumePdfViewer({ fetchBlob, filename, fallbackHint }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let url = null;
    let cancelled = false;
    fetchBlob("png")
      .then((b) => {
        if (cancelled) return;
        url = URL.createObjectURL(b);
        setImageUrl(url);
      })
      .catch(() => !cancelled && setError(true));
    return () => {
      cancelled = true;
      if (url) URL.revokeObjectURL(url);
    };
    // Fetch exactly once per mount — remount (via key) to re-render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleDownload() {
    setDownloading(true);
    try {
      const pdf = await fetchBlob("pdf");
      saveBlob(pdf, filename);
    } catch {
      setError(true);
    } finally {
      setDownloading(false);
    }
  }

  if (error) {
    return (
      <div className="status-error" style={{ marginTop: "var(--s3)" }}>
        ⚠ PDF generation failed — {fallbackHint}
      </div>
    );
  }

  if (!imageUrl) {
    return (
      <div className="loading-state" style={{ padding: "var(--s6) 0" }}>
        <div className="spinner" />
        <span>Rendering your resume…</span>
      </div>
    );
  }

  return (
    <div className="pdf-viewer">
      <img
        className="pdf-viewer-page"
        src={imageUrl}
        alt="Resume PDF preview"
      />
      <div className="pdf-viewer-actions">
        <button
          className="btn btn-primary btn-sm"
          onClick={handleDownload}
          disabled={downloading}
        >
          {downloading ? "Preparing…" : "Download resume"}
        </button>
      </div>
    </div>
  );
}
