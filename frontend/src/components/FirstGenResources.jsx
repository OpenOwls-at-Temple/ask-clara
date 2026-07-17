// Shown only when the student self-identified as first-gen. Deterministic,
// frontend-only content — this flag is never sent to the LLM (see
// ai_specs/auth-security.md) and never gates access to any feature.
const RESOURCES = [
  {
    name: "Temple Career Center",
    href: "https://careercenter.temple.edu",
    desc: "One-on-one advising, career fairs, and employer connections.",
  },
  {
    name: "Student Success Center",
    href: "https://studentsuccess.temple.edu",
    desc: "Academic coaching, tutoring, and writing support.",
  },
  {
    name: "First-Gen @ Temple",
    href: "https://careercenter.temple.edu/identity-and-affinity/first-generation-students",
    desc: "Community, events, and programs for first-generation students.",
  },
];

export default function FirstGenResources() {
  return (
    <div className="form-card" style={{ marginTop: "var(--s6)" }}>
      <div className="form-card-header">
        <div className="form-card-title">First-Generation Resources</div>
        <div className="form-card-desc">
          You're charting new territory — Temple has dedicated support for
          first-gen students, alongside the coaching Clara offers here.
        </div>
      </div>
      <ul style={{ margin: 0, paddingLeft: "var(--s5)" }}>
        {RESOURCES.map((r) => (
          <li key={r.name} style={{ marginBottom: "var(--s3)" }}>
            <a href={r.href} target="_blank" rel="noreferrer">
              {r.name}
            </a>{" "}
            <span style={{ color: "var(--mist)" }}>— {r.desc}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
