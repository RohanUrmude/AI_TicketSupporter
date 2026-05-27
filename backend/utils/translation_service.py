"""
Translation service for multi-language support.
Uses MyMemory Translation API for Indian languages.
Handles large texts by splitting into paragraphs.
"""
import logging
import requests
import os

logger = logging.getLogger(__name__)

# Language code mapping
LANGUAGE_CODES = {
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Gujarati": "gu",
    "Marathi": "mr",
    "Bengali": "bn",
    "Punjabi": "pa",
}

# MyMemory API has a 500 char limit per request, so we split large texts
MAX_CHUNK_SIZE = 400


def split_text_intelligently(text: str, max_size: int = MAX_CHUNK_SIZE) -> list:
    """
    Split text into chunks while preserving paragraph structure.
    Tries to split at paragraph boundaries first, then sentences.
    """
    if len(text) <= max_size:
        return [text]

    chunks = []
    paragraphs = text.split('\n\n')

    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_size:
            if current_chunk:
                current_chunk += '\n\n' + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If single paragraph is too long, split by newline
            if len(para) > max_size:
                lines = para.split('\n')
                temp_chunk = ""
                for line in lines:
                    if len(temp_chunk) + len(line) + 1 <= max_size:
                        temp_chunk += ('' if not temp_chunk else '\n') + line
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = line
                if temp_chunk:
                    chunks.append(temp_chunk)
            else:
                chunks.append(para)
            current_chunk = ""

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def translate_text(text: str, target_language: str) -> str:
    """
    Translate text to target Indian language using MyMemory API.
    Automatically handles large texts by splitting and rejoining.

    Args:
        text: Text to translate (can be up to several KB)
        target_language: Target language name

    Returns:
        Translated text in target language
    """
    if target_language == "English" or target_language not in LANGUAGE_CODES:
        return text

    lang_code = LANGUAGE_CODES[target_language]

    try:
        logger.info(f"Translating {len(text)} chars to {target_language} ({lang_code})")

        # Split large text into manageable chunks
        chunks = split_text_intelligently(text, MAX_CHUNK_SIZE)
        translated_chunks = []

        for chunk in chunks:
            if not chunk.strip():
                translated_chunks.append(chunk)
                continue

            try:
                url = "https://api.mymemory.translated.net/get"
                params = {
                    "q": chunk,
                    "langpair": f"en|{lang_code}"
                }

                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    if data.get("responseStatus") == 200:
                        translated = data.get("responseData", {}).get("translatedText", chunk)
                        translated_chunks.append(translated)
                    else:
                        logger.warning(f"API error for chunk: {data.get('responseDetails')}")
                        translated_chunks.append(chunk)
                else:
                    logger.warning(f"API request failed: {response.status_code}")
                    translated_chunks.append(chunk)

            except Exception as chunk_error:
                logger.warning(f"Chunk translation failed: {chunk_error}")
                translated_chunks.append(chunk)

        # Rejoin chunks with original separators
        final_translation = '\n\n'.join(translated_chunks)
        logger.info(f"Translation successful for {target_language}")
        return final_translation

    except Exception as e:
        logger.warning(f"Translation error for {target_language}: {e}")
        return text
