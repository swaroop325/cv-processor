import pdfplumber
import docx
import re
import json
from io import BytesIO
from fastapi import UploadFile, HTTPException
from openai import OpenAI
import backoff
from app.core.config import settings


class CVProcessor:
    @staticmethod
    async def extract_and_parse(file: UploadFile) -> dict:
        """Extract text from file and parse candidate information"""
        content = await file.read()

        # Normalize content type
        content_type = file.content_type.split(';')[0].strip().lower() if file.content_type else ""

        # Extract text based on file type
        if content_type == "application/pdf":
            raw_text = await CVProcessor._extract_from_pdf(content)
            file_type = "pdf"
        elif content_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "application/docx"
        ]:
            raw_text = await CVProcessor._extract_from_docx(content)
            file_type = "docx"
        elif content_type in ["application/octet-stream", "binary/octet-stream"]:
            # Try to detect from file signature
            if content[:4] == b'%PDF':
                raw_text = await CVProcessor._extract_from_pdf(content)
                file_type = "pdf"
            elif content[:2] == b'PK':  # ZIP archive (DOCX is a ZIP file)
                raw_text = await CVProcessor._extract_from_docx(content)
                file_type = "docx"
            else:
                raise HTTPException(status_code=400, detail="Cannot determine file type from binary content")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}. Only PDF and DOCX files are supported")

        if not raw_text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")

        # Parse information from text
        parsed_info = CVProcessor._parse_cv_info(raw_text)

        return {
            "raw_text": raw_text,
            "file_type": file_type,
            "candidate_name": parsed_info.get("name"),
            "email": parsed_info.get("email"),
            "phone": parsed_info.get("phone"),
            "skills": parsed_info.get("skills"),
            "summary": parsed_info.get("summary")
        }

    @staticmethod
    def _parse_cv_info(text: str) -> dict:
        """Parse candidate information from CV text using OpenAI"""
        # If OpenAI API key is available, use it for better extraction
        if settings.OPENAI_API_KEY:
            try:
                return CVProcessor._parse_with_openai(text)
            except Exception as e:
                print(f"OpenAI parsing failed: {e}, falling back to regex")
                # Fall back to regex if OpenAI fails

        # Fallback: regex-based parsing
        return CVProcessor._parse_with_regex(text)

    @staticmethod
    @backoff.on_exception(
        backoff.expo,
        (Exception,),
        max_tries=3,
        max_time=30
    )
    def _parse_with_openai(text: str) -> dict:
        """Use OpenAI to extract structured data from CV with retry logic"""
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        prompt = f"""Extract the following information from this CV/Resume text. Return ONLY a valid JSON object with these exact fields:
{{
    "name": "candidate full name",
    "email": "email address",
    "phone": "phone number",
    "skills": ["skill1", "skill2", ...],
    "summary": "brief professional summary or objective"
}}

If any field is not found, use null for strings or empty array for skills.

CV Text:
{text[:4000]}"""  # Limit to 4000 chars to avoid token limits

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a CV/Resume parser. Extract structured data and return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            timeout=30
        )

        result = response.choices[0].message.content.strip()

        # Robust JSON extraction (same as old TA-Portal)
        cleaned_output = result

        # Find JSON content within markdown blocks or raw text
        json_start = cleaned_output.find('{')
        json_end = cleaned_output.rfind('}')

        if json_start != -1 and json_end != -1 and json_end > json_start:
            # Extract just the JSON part
            cleaned_output = cleaned_output[json_start:json_end + 1]
        else:
            # Try removing markdown code blocks
            if "```json" in cleaned_output:
                start_idx = cleaned_output.find("```json") + 7
                end_idx = cleaned_output.rfind("```")
                if end_idx > start_idx:
                    cleaned_output = cleaned_output[start_idx:end_idx].strip()
            elif "```" in cleaned_output:
                # Generic code block
                start_idx = cleaned_output.find("```") + 3
                end_idx = cleaned_output.rfind("```")
                if end_idx > start_idx:
                    cleaned_output = cleaned_output[start_idx:end_idx].strip()

        # Final attempt to extract JSON
        json_start = cleaned_output.find('{')
        json_end = cleaned_output.rfind('}')
        if json_start != -1 and json_end != -1:
            cleaned_output = cleaned_output[json_start:json_end + 1]

        if not cleaned_output:
            raise ValueError("No JSON content found in OpenAI response")

        parsed = json.loads(cleaned_output)

        # Convert None to proper values
        info = {
            "name": parsed.get("name") or None,
            "email": parsed.get("email") or None,
            "phone": parsed.get("phone") or None,
            "skills": parsed.get("skills") or [],
            "summary": parsed.get("summary") or None
        }

        return info

    @staticmethod
    def _parse_with_regex(text: str) -> dict:
        """Fallback regex-based parsing"""
        info = {}

        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text, re.IGNORECASE)
        if emails:
            info["email"] = emails[0].strip().lower()

        # Extract phone
        phone_pattern = r'[\+]?[(]?\d{1,4}[)]?[-\s\.]?\(?\d{1,3}\)?[-\s\.]?\d{1,4}[-\s\.]?\d{1,4}[-\s\.]?\d{1,9}'
        phones = re.findall(phone_pattern, text)
        if phones:
            phone = phones[0].strip()
            if len(phone) >= 10:
                info["phone"] = phone

        # Extract name (first line)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            for line in lines[:5]:
                if 'name' in line.lower() and ':' in line:
                    name = line.split(':', 1)[1].strip()
                    if name and len(name.split()) >= 2:
                        info["name"] = name
                        break

            if "name" not in info and lines[0]:
                first_line = lines[0]
                if 2 <= len(first_line.split()) <= 4 and re.match(r'^[A-Za-z\s]+$', first_line):
                    info["name"] = first_line

        # Extract skills
        skills_section = re.search(r'(?:skills?|technical skills?|competencies)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)',
                                   text, re.IGNORECASE | re.DOTALL)
        if skills_section:
            skills_text = skills_section.group(1)
            skills = re.split(r'[,;•\|\n]', skills_text)
            skills = [s.strip() for s in skills if s.strip() and len(s.strip()) > 2 and len(s.strip()) < 50]
            if skills:
                info["skills"] = skills[:20]

        # Extract summary
        summary_match = re.search(r'(?:summary|objective|profile|about)[:\s]+(.*?)(?:\n\n|experience|education|skills)',
                                 text, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
            if len(summary) > 50 and len(summary) < 1000:
                info["summary"] = summary

        return info

    @staticmethod
    async def _extract_from_pdf(content: bytes) -> str:
        try:
            with pdfplumber.open(BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract PDF: {str(e)}")

    @staticmethod
    async def _extract_from_docx(content: bytes) -> str:
        try:
            doc = docx.Document(BytesIO(content))
            text = "\n".join([p.text for p in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to extract DOCX: {str(e)}")
