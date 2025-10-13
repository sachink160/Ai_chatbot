from typing import List, Dict, Any
import os
import json
import base64
import fitz
from docx import Document as DocxDocument
from sqlalchemy.orm import Session
from openai import OpenAI

from app.models import Resume, JobRequirement, ResumeMatch
from app.logger import get_logger

logger = get_logger(__name__)


class ResumeService:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)

    def _extract_text_from_pdf(self, pdf_path: str, model: str = "gpt-4o-mini") -> str:
        doc = fitz.open(pdf_path)
        text_accumulator = []
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                text_accumulator.append(text)
            else:
                pix = page.get_pixmap(dpi=200)
                img_b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text clearly from this resume image."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                        ],
                    }],
                )
                text_accumulator.append(response.choices[0].message.content.strip())
        doc.close()
        return "\n".join(text_accumulator).strip()

    def _extract_text(self, file_path: str, model: str = "gpt-4o-mini") -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return self._extract_text_from_pdf(file_path, model)
        if ext == ".docx":
            d = DocxDocument(file_path)
            return "\n".join(p.text for p in d.paragraphs).strip()
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        raise ValueError(f"Unsupported file type: {ext}")

    def _parse_resume(self, text: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        prompt = (
            "Parse the following resume text into strict JSON with keys: "
            "name, email, phone, location, total_experience_years, education (list), skills (list of strings), "
            "work_experiences (list of {company, title, start_date, end_date, responsibilities}), certifications (list).\n\n"
            "Return only JSON.\n\nResume:\n" + text
        )
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
            if content.endswith("```"):
                content = "\n".join(content.split("\n")[:-1])
        try:
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse resume JSON: {e}")
            return {"raw_output": content, "error": str(e)}

    def _score_resume_against_requirement(self, parsed_resume: Dict[str, Any], requirement_json: Dict[str, Any], model: str = "gpt-4o-mini") -> Dict[str, Any]:
        prompt = (
            "You are a recruiter. Score the candidate against the requirement on a 0-100 scale.\n"
            "Breakdown by criteria with sub-scores and a short rationale. Return strict JSON with keys: "
            "overall_score (0-100), rationale, criteria_scores (list of {criterion, score, notes}).\n\n"
            f"Requirement JSON:\n{json.dumps(requirement_json)}\n\n"
            f"Candidate JSON:\n{json.dumps(parsed_resume)}\n"
        )
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
            if content.endswith("```"):
                content = "\n".join(content.split("\n")[:-1])
        try:
            return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse score JSON: {e}")
            return {"overall_score": 0, "rationale": "Parse error", "criteria_scores": [], "error": str(e)}

    def ingest_resume(self, db: Session, *, user_id: str, file_path: str, original_filename: str, model: str = "gpt-4o-mini") -> Resume:
        text = self._extract_text(file_path, model)
        parsed = self._parse_resume(text, model)
        resume = Resume(
            user_id=user_id,
            original_filename=original_filename,
            file_path=file_path,
            file_type=os.path.splitext(file_path)[1].lower(),
            extracted_text=text,
            parsed_profile=json.dumps(parsed),
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        return resume

    def match_resumes(self, db: Session, *, user_id: str, requirement: JobRequirement, resume_ids: List[str]) -> List[ResumeMatch]:
        req_json = json.loads(requirement.requirement_json)
        matches: List[ResumeMatch] = []
        for rid in resume_ids:
            resume = db.query(Resume).filter(Resume.id == rid, Resume.user_id == user_id).first()
            if not resume:
                continue
            try:
                parsed = json.loads(resume.parsed_profile) if resume.parsed_profile else {}
            except Exception:
                parsed = {"raw_profile": resume.parsed_profile}
            scored = self._score_resume_against_requirement(parsed, req_json, requirement.gpt_model)
            score = float(scored.get("overall_score", 0))
            match = ResumeMatch(
                user_id=user_id,
                requirement_id=requirement.id,
                resume_id=resume.id,
                score=score,
                rationale=scored.get("rationale"),
                match_metadata=json.dumps(scored.get("criteria_scores", [])),
            )
            db.add(match)
            matches.append(match)
        db.commit()
        for m in matches:
            db.refresh(m)
        return matches

