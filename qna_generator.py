"""
QnA Generator Module
=====================
Uses Google Gemini API to generate Question-Answer pairs from document text
and translate them into English, Hindi, and Marathi.
"""

import json
import re
import google.generativeai as genai


def _configure_gemini(api_key: str):
    """Configure the Gemini API with the provided key."""
    genai.configure(api_key=api_key)


def _clean_json_response(response_text: str) -> str:
    """
    Clean the Gemini response to extract valid JSON.
    Handles markdown code blocks and extra whitespace.
    """
    text = response_text.strip()
    # Remove markdown code fences
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return text


def _parse_qna_response(response_text: str) -> list[dict]:
    """
    Parse the Gemini response into a list of QnA dicts.
    
    Returns:
        List of dicts with 'question' and 'answer' keys.
    """
    cleaned = _clean_json_response(response_text)
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "qna" in data:
            return data["qna"]
        elif isinstance(data, dict) and "qna_pairs" in data:
            return data["qna_pairs"]
        else:
            return [data]
    except json.JSONDecodeError:
        # Fallback: try to extract QnA pairs using regex
        pairs = []
        q_pattern = re.findall(r'["\']?[Qq]uestion["\']?\s*:\s*["\'](.+?)["\']', cleaned)
        a_pattern = re.findall(r'["\']?[Aa]nswer["\']?\s*:\s*["\'](.+?)["\']', cleaned)
        for q, a in zip(q_pattern, a_pattern):
            pairs.append({"question": q, "answer": a})
        if pairs:
            return pairs
        raise ValueError(f"Could not parse QnA response. Raw response:\n{response_text[:500]}")


def generate_qna_english(text: str, api_key: str, num_pairs: int = 10) -> list[dict]:
    """
    Generate Question-Answer pairs in English from the given document text.
    
    Args:
        text: The extracted document text.
        api_key: Google Gemini API key.
        num_pairs: Number of QnA pairs to generate.
    
    Returns:
        List of dicts with 'question' and 'answer' keys.
    """
    _configure_gemini(api_key)
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Truncate text if too long (Gemini has context limits)
    max_chars = 30000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... Document truncated for processing ...]"
    
    prompt = f"""You are an expert Question-Answer pair generator. Analyze the following document text carefully and generate exactly {num_pairs} high-quality, contextually relevant Question-Answer pairs in English.

RULES:
1. Questions must be directly answerable from the document content.
2. Answers must be accurate, concise, and derived from the document.
3. Cover different sections/topics of the document.
4. Include a mix of factual, conceptual, and analytical questions.
5. Questions should be clear and well-formed.
6. Answers should be complete sentences, not single words.

DOCUMENT TEXT:
\"\"\"
{text}
\"\"\"

OUTPUT FORMAT: Return ONLY a valid JSON array with exactly {num_pairs} objects. Each object must have "question" and "answer" keys.
Example:
[
  {{"question": "What is ...?", "answer": "The answer is ..."}},
  {{"question": "How does ...?", "answer": "It works by ..."}}
]

Generate exactly {num_pairs} QnA pairs now:"""

    response = model.generate_content(prompt)
    return _parse_qna_response(response.text)


def translate_qna(qna_pairs: list[dict], target_language: str, api_key: str) -> list[dict]:
    """
    Translate English QnA pairs to the target language using Gemini.
    
    Args:
        qna_pairs: List of English QnA dicts.
        target_language: Target language name ("Hindi" or "Marathi").
        api_key: Google Gemini API key.
    
    Returns:
        List of translated QnA dicts.
    """
    _configure_gemini(api_key)
    
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # Build the QnA text for translation
    qna_json = json.dumps(qna_pairs, ensure_ascii=False, indent=2)
    
    prompt = f"""You are an expert translator. Translate ALL the following English Question-Answer pairs into {target_language}.

RULES:
1. Translate BOTH the questions AND the answers into {target_language}.
2. Maintain the exact meaning and context of each QnA pair.
3. Use natural, grammatically correct {target_language}.
4. Do NOT add or remove any QnA pairs.
5. Do NOT transliterate — use proper {target_language} script ({"Devanagari" if target_language in ["Hindi", "Marathi"] else target_language}).
6. Keep technical terms as-is if no standard translation exists.

ENGLISH QnA PAIRS:
{qna_json}

OUTPUT FORMAT: Return ONLY a valid JSON array with the translated objects. Each object must have "question" and "answer" keys.
Translate all {len(qna_pairs)} pairs now:"""

    response = model.generate_content(prompt)
    translated = _parse_qna_response(response.text)
    
    # Ensure we have the same number of pairs
    if len(translated) != len(qna_pairs):
        # Pad or truncate to match
        if len(translated) < len(qna_pairs):
            for i in range(len(translated), len(qna_pairs)):
                translated.append({
                    "question": qna_pairs[i]["question"],
                    "answer": qna_pairs[i]["answer"]
                })
        else:
            translated = translated[:len(qna_pairs)]
    
    return translated


def generate_multilingual_qna(
    text: str, 
    api_key: str, 
    num_pairs: int = 10,
    progress_callback=None
) -> dict:
    """
    Orchestrator function that generates QnA pairs in all three languages.
    
    Args:
        text: The extracted document text.
        api_key: Google Gemini API key.
        num_pairs: Number of QnA pairs to generate.
        progress_callback: Optional callback function for progress updates.
                          Called with (step_number, total_steps, message).
    
    Returns:
        Dict with keys 'english', 'hindi', 'marathi', each containing
        a list of QnA dicts.
    """
    results = {}
    
    # Step 1: Generate English QnA pairs
    if progress_callback:
        progress_callback(1, 3, "🔍 Generating English QnA pairs from document...")
    results["english"] = generate_qna_english(text, api_key, num_pairs)
    
    # Step 2: Translate to Hindi
    if progress_callback:
        progress_callback(2, 3, "🇮🇳 Translating to Hindi (हिन्दी)...")
    results["hindi"] = translate_qna(results["english"], "Hindi", api_key)
    
    # Step 3: Translate to Marathi
    if progress_callback:
        progress_callback(3, 3, "🇮🇳 Translating to Marathi (मराठी)...")
    results["marathi"] = translate_qna(results["english"], "Marathi", api_key)
    
    return results
