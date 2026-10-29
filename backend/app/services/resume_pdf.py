"""Generate a compact, ATS-friendly PDF from a tailored resume."""

import io
import re
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)


SECTION_HEADINGS = {
    "summary",
    "professional summary",
    "profile",
    "objective",
    "education",
    "experience",
    "work experience",
    "professional experience",
    "skills",
    "technical skills",
    "projects",
    "personal projects",
    "certifications",
    "certificates",
    "achievements",
    "accomplishments",
    "internships",
    "internship experience",
    "publications",
    "awards",
    "languages",
    "volunteer experience",
    "volunteering",
}

DATE_PATTERN = re.compile(
    r"^(?:"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+\d{4}"
    r"|\d{4}"
    r")"
    r"(?:\s*[-–—]\s*(?:"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|"
    r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|"
    r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+"
    r")?(?:\d{4}|Present|Current|Ongoing))?$",
    re.IGNORECASE,
)

BULLET_PATTERN = re.compile(r"^(?:[-*•]|\d+[.)])\s+(.+)$")
MARKDOWN_HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$")

URL_PATTERN = re.compile(r"https?://[^\s<]+", re.IGNORECASE)

PHONE_PATTERN = re.compile(r"\+?\d[\d\s()\-]{7,}\d")


def _inline_markup(text: str) -> str:
    """Escape text safely and support Markdown emphasis and clickable URLs."""
    text = escape(text)

    # Support bold Markdown.
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
    )

    # Support italic Markdown.
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        r"<i>\1</i>",
        text,
    )
    text = re.sub(
        r"(?<!_)_([^_]+)_(?!_)",
        r"<i>\1</i>",
        text,
    )

    # Support inline code.
    text = re.sub(
        r"`([^`]+)`",
        r"<font name='Courier'>\1</font>",
        text,
    )

    # Make HTTP(S) URLs clickable in the generated PDF.
    def make_clickable(match: re.Match) -> str:
        matched_url = match.group(0)
        url = matched_url.rstrip(".,;:)")
        trailing = matched_url[len(url):]
        parsed = urlparse(url)

        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            return matched_url

        safe_url = escape(url, {'"': "&quot;", "'": "&apos;"})

        return (
            f'<link href="{safe_url}" color="blue">'
            f"{url}</link>{trailing}"
        )

    return URL_PATTERN.sub(make_clickable, text)


def _clean_line(line: str) -> str:
    """Remove Markdown heading markers without merging adjacent lines."""
    line = line.strip()
    match = MARKDOWN_HEADING_PATTERN.match(line)

    if match:
        return match.group(1).strip()

    return line


def _is_section_heading(line: str) -> bool:
    """Identify recognized resume section headings."""
    cleaned = _clean_line(line).strip().rstrip(":")
    normalized = re.sub(r"[*_`]", "", cleaned).strip().lower()
    return normalized in SECTION_HEADINGS


def _is_contact_line(line: str) -> bool:
    """Identify common contact details in a resume header."""
    lower_line = line.lower()

    return (
        "@" in line
        or "linkedin.com/" in lower_line
        or "github.com/" in lower_line
        or "www." in lower_line
        or "http://" in lower_line
        or "https://" in lower_line
        or "|" in line
        or PHONE_PATTERN.search(line) is not None
    )


def _normalize_contact_line(line: str) -> str:
    """Remove redundant separators around a contact line."""
    return line.strip().strip("|").strip()


def _prepare_resume_lines(raw_lines: list[str]) -> list[str]:
    """Normalize resume lines and move header details before section headings."""
    lines = [_clean_line(line).strip() for line in raw_lines]
    lines = [line for line in lines if line]

    if not lines:
        raise ValueError("Resume text cannot be empty.")

    # Find the first recognized section heading.
    heading_index = next(
        (
            i for i, line in enumerate(lines)
            if _is_section_heading(line)
        ),
        None,
    )

    if heading_index is None:
        return lines

    # If the resume already starts with a name, gather contact details
    # appearing before the first section heading.
    if heading_index > 0:
        header = lines[:heading_index]
        content = lines[heading_index:]

        name = header[0]
        contacts = []

        for line in header[1:]:
            if _is_contact_line(line):
                contacts.append(line)

        return [name, *contacts, *content]

    # Handle the malformed ordering seen in the generated PDF:
    # PROFESSIONAL SUMMARY
    # Aryan Kumar Prajapati
    # phone | email |
    # LinkedIn URL
    # | GitHub URL
    if (
        len(lines) >= 3
        and not _is_contact_line(lines[1])
        and _is_contact_line(lines[2])
    ):
        heading = lines[0]
        name = lines[1]
        contacts = []
        index = 2

        while index < len(lines) and _is_contact_line(lines[index]):
            contact = _normalize_contact_line(lines[index])
            if contact:
                contacts.append(contact)
            index += 1

        # Merge contact details and remove empty separators.
        parts = []
        for contact in contacts:
            parts.extend(
                part.strip()
                for part in contact.split("|")
                if part.strip()
            )

        contact_line = " | ".join(dict.fromkeys(parts))

        return [
            name,
            contact_line,
            heading,
            *lines[index:],
        ]

    return lines


def generate_resume_pdf(resume_text: str) -> bytes:
    """Convert resume text or Markdown into a compact US Letter PDF."""
    if not resume_text or not resume_text.strip():
        raise ValueError("Resume text cannot be empty.")

    raw_lines = (
        resume_text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .split("\n")
    )

    lines = _prepare_resume_lines(raw_lines)

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.48 * inch,
        rightMargin=0.48 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.35 * inch,
        title="Tailored Resume",
        author="Resume Intelligence System",
        pageCompression=1,
    )

    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ResumeName",
            parent=styles["Title"],
            fontName="Times-Bold",
            fontSize=15,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceBefore=0,
            spaceAfter=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeContact",
            parent=styles["Normal"],
            fontName="Times-Roman",
            fontSize=8.3,
            leading=9.2,
            alignment=TA_CENTER,
            textColor=colors.black,
            spaceBefore=0,
            spaceAfter=2,
            splitLongWords=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeSection",
            parent=styles["Heading2"],
            fontName="Times-Bold",
            fontSize=10.5,
            leading=11,
            textColor=colors.black,
            spaceBefore=3,
            spaceAfter=1,
            keepWithNext=True,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeBody",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            fontSize=9.2,
            leading=10,
            textColor=colors.black,
            spaceBefore=0,
            spaceAfter=0.8,
            splitLongWords=1,
            allowWidows=0,
            allowOrphans=0,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeBullet",
            parent=styles["ResumeBody"],
            leftIndent=10,
            firstLineIndent=-7,
            spaceAfter=0.5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeEntryTitle",
            parent=styles["ResumeBody"],
            fontName="Times-Bold",
            spaceBefore=1,
            spaceAfter=1,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ResumeDate",
            parent=styles["ResumeBody"],
            alignment=TA_RIGHT,
            fontSize=8.8,
            leading=9.5,
            spaceBefore=0,
            spaceAfter=0.5,
        )
    )

    story = []
    first_content_line = True

    available_width = (
        letter[0] - document.leftMargin - document.rightMargin
    )

    i = 0

    while i < len(lines):
        original_line = lines[i]
        line = original_line.strip()

        is_markdown_heading = bool(
            MARKDOWN_HEADING_PATTERN.match(original_line)
        )

        # The first non-section line is rendered as the candidate's name.
        if first_content_line:
            first_content_line = False

            if (
                not _is_section_heading(line)
                and not is_markdown_heading
                and not _is_contact_line(line)
            ):
                story.append(
                    Paragraph(
                        _inline_markup(line),
                        styles["ResumeName"],
                    )
                )
                i += 1
                continue

        # Render recognized section headings.
        if _is_section_heading(line) or is_markdown_heading:
            story.append(
                Paragraph(
                    _inline_markup(line.rstrip(":")),
                    styles["ResumeSection"],
                )
            )
            i += 1
            continue

        # Render bullets without changing their text.
        bullet_match = BULLET_PATTERN.match(line)

        if bullet_match:
            story.append(
                Paragraph(
                    "&#8226; " + _inline_markup(bullet_match.group(1)),
                    styles["ResumeBullet"],
                )
            )
            i += 1
            continue

        # Pair a title with the immediately following date-only line.
        if (
            i + 1 < len(lines)
            and DATE_PATTERN.fullmatch(lines[i + 1].strip())
            and not DATE_PATTERN.fullmatch(line)
            and not _is_section_heading(lines[i + 1])
        ):
            title_cell = Paragraph(
                _inline_markup(line),
                styles["ResumeEntryTitle"],
            )

            date_cell = Paragraph(
                _inline_markup(lines[i + 1].strip()),
                styles["ResumeDate"],
            )

            table = Table(
                [[title_cell, date_cell]],
                colWidths=[
                    available_width * 0.72,
                    available_width * 0.28,
                ],
                hAlign="LEFT",
            )

            table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )

            story.append(table)
            i += 2
            continue

        # Render unmatched standalone dates without attaching them elsewhere.
        if DATE_PATTERN.fullmatch(line):
            story.append(
                Paragraph(
                    _inline_markup(line),
                    styles["ResumeDate"],
                )
            )
            i += 1
            continue

        # Render contact details near the beginning using centered styling.
        is_contact = (
            len(story) <= 3
            and len(line) <= 240
            and _is_contact_line(line)
        )

        style = (
            styles["ResumeContact"]
            if is_contact
            else styles["ResumeBody"]
        )

        story.append(
            Paragraph(
                _inline_markup(line),
                style,
            )
        )
        i += 1

    document.build(story)
    return buffer.getvalue()
