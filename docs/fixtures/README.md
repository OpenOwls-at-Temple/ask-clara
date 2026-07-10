# Test Fixtures

## `synthetic-resume.docx`

A fully fictional resume for **manual local testing** of the intake → assessment →
resume-generation flow. "Jordan Rivera" is not a real person; the contact block uses
`example.edu` and a 555 phone number (kept in on purpose so the PII-stripping path is
exercised before any LLM call).

**Why it exists:** the provider data policy (`ai_specs/llm-integration.md` → Privacy &
Safety) forbids sending real resume or LinkedIn content through non-Anthropic providers
(Gemini, DeepSeek). If your local `.env` uses a free-tier Gemini key or a DeepSeek key,
this fixture is the **only** resume you should upload. Real personal data is allowed
locally only through your own Anthropic key.

The profile is a Temple CST undergrad (CS major, expected May 2027) so assessments
exercise the `undergrad` degree-level branch with a realistic mix of experience,
projects, and skills.

To regenerate or vary it, edit and rerun a `python-docx` script against this content
(python-docx is already in `backend/requirements.txt`); keep all names, employers, and
contact details clearly fictional.
