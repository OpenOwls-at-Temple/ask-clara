"""PII stripping and token-budget clipping in the LLM orchestrator.

A regex failure in strip_contact_block would silently leak student PII
to a third-party LLM provider, so these assertions are strict.
"""

from app.llm.orchestrator import (
    MAX_INPUT_CHARS,
    build_assessment_context,
    build_job_match_context,
    build_plan_context,
    strip_contact_block,
    trim_resume_text,
)

SAMPLE_RESUME = """John Doe
john.doe@temple.edu
(215) 555-1234
1801 N Broad St, Philadelphia, PA 19122
EXPERIENCE
Software Engineering Intern at Comcast
Built dashboards in React and Python"""


def test_strip_contact_block_removes_email_lines():
    cleaned = strip_contact_block(SAMPLE_RESUME)
    assert "john.doe@temple.edu" not in cleaned
    assert "@" not in cleaned


def test_strip_contact_block_removes_phone_lines():
    cleaned = strip_contact_block(SAMPLE_RESUME)
    assert "555-1234" not in cleaned
    assert "555-1234" not in strip_contact_block("Cell: 215-555-1234\nSkills: SQL")


def test_strip_contact_block_removes_multiword_street_address():
    cleaned = strip_contact_block(SAMPLE_RESUME)
    assert "1801 N Broad St" not in cleaned
    assert "123 Main St" not in strip_contact_block("123 Main St\nObjective: SWE")


def test_strip_contact_block_keeps_experience_lines():
    cleaned = strip_contact_block(SAMPLE_RESUME)
    assert "Software Engineering Intern at Comcast" in cleaned
    assert "Built dashboards in React and Python" in cleaned


def test_trim_resume_text_caps_length():
    text = "experience line\n" * 2000  # well over the cap, no PII
    assert len(trim_resume_text(text)) <= MAX_INPUT_CHARS


def test_trim_resume_text_strips_pii_before_capping():
    text = "student@temple.edu\n" + "a" * (MAX_INPUT_CHARS + 500)
    assert "@" not in trim_resume_text(text)


def test_build_assessment_context_strips_pii_from_resume_and_linkedin():
    profile = {
        "degree_level": "undergrad",
        "major_program": "Computer Science",
        "track": "industry",
        "expected_graduation": None,
        "target_roles": [
            {"rank": 2, "title": "Data Analyst"},
            {"rank": 1, "title": "Software Engineer"},
        ],
    }
    linkedin = "reach me at jd@example.com\nAspiring product manager"
    ctx = build_assessment_context(profile, SAMPLE_RESUME, linkedin)

    assert "@" not in ctx["resume_text"]
    assert "@" not in ctx["linkedin_summary"]
    assert "Aspiring product manager" in ctx["linkedin_summary"]
    # target roles are ordered by rank
    assert ctx["target_roles"] == ["Software Engineer", "Data Analyst"]


def test_build_assessment_context_handles_missing_linkedin():
    profile = {"target_roles": []}
    ctx = build_assessment_context(profile, "resume", None)
    assert ctx["linkedin_summary"] is None


def test_build_plan_context_never_includes_resume_text():
    profile = {
        "degree_level": "grad",
        "major_program": "Data Science",
        "track": "industry",
        "target_roles": [{"rank": 1, "title": "ML Engineer"}],
    }
    assessment = {
        "strengths": ["Python"],
        "gaps": ["Cloud"],
        "recommendations": ["Take AWS course"],
        "raw_transcript": "should not pass through",
    }
    ctx = build_plan_context(profile, assessment)
    assert "resume_text" not in ctx
    assert ctx["assessment"] == {
        "strengths": ["Python"],
        "gaps": ["Cloud"],
        "recommendations": ["Take AWS course"],
    }


def test_build_job_match_context_sends_only_posting_metadata():
    profile = {"target_roles": []}
    postings = [
        {
            "title": "Junior Analyst",
            "employer": "Vanguard",
            "location": "Malvern, PA",
            "description": "email hr@vanguard.com to apply",
            "url": "https://example.com/job/1",
        }
    ]
    ctx = build_job_match_context(profile, postings)
    assert ctx["postings"] == [
        {
            "index": 0,
            "title": "Junior Analyst",
            "employer": "Vanguard",
            "location": "Malvern, PA",
        }
    ]
