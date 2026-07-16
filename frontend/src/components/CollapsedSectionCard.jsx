export default function CollapsedSectionCard({ title, summary, onEdit }) {
  return (
    <div className="form-card-collapsed">
      <div className="form-card-collapsed-left">
        <div className="form-card-check">✓</div>
        <div>
          <div
            className="form-card-title"
            style={{ marginBottom: "var(--s1)" }}
          >
            {title}
          </div>
          <div className="form-card-collapsed-summary">{summary}</div>
        </div>
      </div>
      <button
        className="btn btn-secondary btn-sm"
        type="button"
        onClick={onEdit}
      >
        Edit
      </button>
    </div>
  );
}
