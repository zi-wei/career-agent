from career_agent.materials.models import ResumeVariant
from career_agent.materials.schemas import ResumeSection


def render_resume_markdown(resume: ResumeVariant) -> str:
    lines = [f"# {resume.target_title}", "", resume.summary.strip(), ""]
    for raw_section in resume.sections:
        section = ResumeSection.model_validate(raw_section)
        lines.extend([f"## {section.title}", ""])
        lines.extend(f"- {bullet.text}" for bullet in section.bullets)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
