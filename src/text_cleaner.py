import re
import unicodedata
from typing import List
from src.pdf_processor import ExtractedPage


class TextCleaner:
    """
    Cleans raw extracted text from digital and OCR pipelines.
    Preserves document structure (headings, numbering, bullet points, milestones, tables).
    """

    # Common recurring header/footer artifacts in reports
    HEADER_FOOTER_PATTERNS = [
        r"(?i)^page\s+\d+\s+(of\s+\d+)?$",
        r"(?i)^terms\s+of\s+reference$",
        r"(?i)^project\s+requirements\s+document$",
        r"(?i)^confidential\s+document$",
        r"(?i)^strictly\s+confidential$"
    ]

    @classmethod
    def clean_page_text(cls, text: str) -> str:
        """
        Normalizes unicode, removes isolated header/footer artifacts,
        and cleans whitespace while maintaining paragraph breaks and lists.
        """
        if not text:
            return ""

        # Normalize unicode to NFKC standard
        text = unicodedata.normalize("NFKC", text)

        # Replace non-standard whitespace/tabs
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)

        lines = text.split("\n")
        cleaned_lines: List[str] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                cleaned_lines.append("")
                continue

            # Check if line matches common recurring header/footer artifact
            is_artifact = any(re.match(pat, line_str) for pat in cls.HEADER_FOOTER_PATTERNS)
            if is_artifact:
                continue

            cleaned_lines.append(line_str)

        # Join lines and collapse 3+ consecutive newlines into 2
        joined = "\n".join(cleaned_lines)
        joined = re.sub(r"\n{3,}", "\n\n", joined)
        return joined.strip()

    @classmethod
    def format_document_with_page_citations(cls, pages: List[ExtractedPage]) -> str:
        """
        Assembles all cleaned pages into a unified document string,
        explicitly tagging page numbers to support grounding and citations.
        """
        formatted_sections: List[str] = []

        for page in pages:
            cleaned = cls.clean_page_text(page.text)
            if cleaned:
                method_tag = f"[{page.extraction_method}]"
                section_header = f"--- [PAGE {page.page_number} {method_tag}] ---"
                formatted_sections.append(f"{section_header}\n{cleaned}\n")

        return "\n".join(formatted_sections)
