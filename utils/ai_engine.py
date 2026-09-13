"""
ai_engine.py
-------------
Handles all AI logic (prompt building + Groq API calls) and PDF generation.
Kept separate from app.py so the UI layer stays clean (separation of concerns).
"""

import os
import io
from groq import Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

MODEL_NAME = "openai/gpt-oss-20b"


def get_client(api_key: str) -> Groq:
    """Create and return a Groq client instance."""
    return Groq(api_key=api_key)


# Shared tone/format rules applied to every prompt so all three tabs feel consistent.
STYLE_RULES = """
STRICT STYLE RULES (always follow):
- Reply ONLY in simple, plain English. Never switch to Urdu, Roman Urdu, or any other language.
- Write like you're texting a friend who knows skincare - warm, casual, easy to understand.
- No jargon-heavy explanations. If you must name an ingredient, explain it in one short plain phrase.
- NO markdown tables, NO multiple headers/sections, NO "Bottom line" style summaries.
- Use short bullet points only, max 5-6 bullets total. Each bullet must be ONE short line (under 15 words).
- Total response under 100 words. Be direct and to the point - no filler, no repeating the question back.
"""


def build_routine_prompt(age: int, skin: str, season: str, concerns: list[str]) -> str:
    """Builds the prompt for the personalized routine generator."""
    return f"""
    Act as a friendly skincare expert. Profile: {age}y, {skin} skin, {season} season.
    Concerns: {', '.join(concerns)}.
    Give a routine using this exact format, with a short reason for each step:

    Morning:
    1. [Product/brand - Jenpharm, Primary, or Vince] - why this step matters (under 12 words)
    2. ...
    3. ...

    Night:
    1. [Product/brand] - why this step matters (under 12 words)
    2. ...
    3. ...

    Tip: 1 climate-specific tip with a one-line reason why it helps.

    STYLE RULES:
    - Reply ONLY in simple, plain English. Never switch to Urdu, Roman Urdu, or any other language.
    - Friendly, easy-to-understand tone - like a knowledgeable friend explaining, not a textbook.
    - Each step's "why" should be practical and specific to their concerns, not generic.
    - No markdown tables. Numbered lists only, as shown above.
    - Total response under 180 words.
    """


def build_chat_prompt(query: str) -> str:
    """Builds the prompt for the chatbot / analysis features."""
    return f"""
    You are 'BellaAI', a friendly skincare expert chatting with a regular person (not a doctor).
    Answer this question simply and safely for the Pakistani climate: {query}
    If it sounds like a serious or emergency skin issue, tell them to see a dermatologist - in one short line, not a whole section.
    {STYLE_RULES}
    """


def call_skincare_ai(api_key: str, prompt_type: str, **kwargs) -> str:
    """
    Central function that talks to the Groq API.
    prompt_type: "routine" or "chat"
    kwargs: passed to the relevant prompt builder
    """
    if not api_key:
        return "⚠️ GROQ_API_KEY not found. Please add it to your .env file or Streamlit secrets."

    client = get_client(api_key)

    if prompt_type == "routine":
        prompt = build_routine_prompt(
            age=kwargs["age"],
            skin=kwargs["skin"],
            season=kwargs["season"],
            concerns=kwargs["concerns"],
        )
    else:
        prompt = build_chat_prompt(kwargs["query"])

    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_NAME,
            temperature=0.6,
            max_tokens=600,
            reasoning_effort="low",
        )
        content = completion.choices[0].message.content
        if not content:
            return "⚠️ Got an empty response from the AI. Please try asking again."
        return content
    except Exception as e:
        return f"❌ AI service error: {str(e)}. Please try again in a moment."


def generate_pdf(title: str, content: str) -> bytes:
    """
    Converts a routine/analysis text result into a downloadable PDF.
    Returns raw PDF bytes ready for st.download_button.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 16),
    ]

    for line in content.split("\n"):
        clean_line = line.strip()
        if clean_line:
            story.append(Paragraph(clean_line, styles["Normal"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()