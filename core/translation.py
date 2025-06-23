"""Translation using deep-translator."""
from typing import List
from core.constants import LANGUAGE_CODES
from deep_translator import GoogleTranslator

def translate_text(text: str, target_language: str) -> str:
    """Translate text to the target language."""
    try:
        lang_code = get_language_code(target_language)
        return GoogleTranslator(target=lang_code).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def get_language_code(language: str) -> str:
    """Get ISO code for a language name."""
    return LANGUAGE_CODES.get(language, 'en')

def batch_translate_texts(texts: List[str], target_language: str) -> List[str]:
    """Translate a list of texts to the target language."""
    lang_code = get_language_code(target_language)
    try:
        # GoogleTranslator supports batch translation via list input
        return GoogleTranslator(target=lang_code).translate(texts)
    except Exception as e:
        print(f"Batch translation error: {e}")
        # Return original texts if translation fails
        return texts 