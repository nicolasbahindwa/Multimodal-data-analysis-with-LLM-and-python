from mcp.server.fastmcp import FastMCP

# MPC server instance name "Translator"
mcp = FastMCP("Translator")

# Dictionary of language codes
LANGUAGE_CODES = {
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "japanese": "ja",
    "chinese": "zh",
    "korean": "ko",
    "russian": "ru",
    "arabic": "ar"
}

# Basic translations for common phrases (in a real implementation, this would use a translation API)
TRANSLATIONS = {
    "hello": {
        "es": "hola",
        "fr": "bonjour",
        "de": "hallo",
        "it": "ciao",
        "pt": "olá",
        "ja": "こんにちは",
        "zh": "你好",
        "ko": "안녕하세요",
        "ru": "привет",
        "ar": "مرحبا"
    },
    "goodbye": {
        "es": "adiós",
        "fr": "au revoir",
        "de": "auf wiedersehen",
        "it": "arrivederci",
        "pt": "adeus",
        "ja": "さようなら",
        "zh": "再见",
        "ko": "안녕히 가세요",
        "ru": "до свидания",
        "ar": "وداعا"
    },
    "thank you": {
        "es": "gracias",
        "fr": "merci",
        "de": "danke",
        "it": "grazie",
        "pt": "obrigado",
        "ja": "ありがとう",
        "zh": "谢谢",
        "ko": "감사합니다",
        "ru": "спасибо",
        "ar": "شكرا"
    },
    "how are you": {
        "es": "¿cómo estás?",
        "fr": "comment vas-tu?",
        "de": "wie geht es dir?",
        "it": "come stai?",
        "pt": "como vai você?",
        "ja": "お元気ですか？",
        "zh": "你好吗？",
        "ko": "어떻게 지내세요?",
        "ru": "как дела?",
        "ar": "كيف حالك؟"
    }
}

# Translation function
@mcp.tool()
def translate(text: str, target_language: str) -> str:
    """
    Translate text to the target language
    
    Args:
        text: The text to translate
        target_language: The language to translate to (e.g., "spanish", "french")
    
    Returns:
        The translated text
    """
    # Convert target language to lowercase for case-insensitive matching
    target_language = target_language.lower()
    
    # Get the language code
    lang_code = LANGUAGE_CODES.get(target_language)
    if not lang_code:
        return f"Error: Unsupported language '{target_language}'. Supported languages are: {', '.join(LANGUAGE_CODES.keys())}"
    
    # Simple translation for demonstration purposes
    # In a real implementation, this would use a translation API
    text_lower = text.lower()
    
    # Check if text is in our basic dictionary
    for key, translations in TRANSLATIONS.items():
        if key in text_lower:
            if lang_code in translations:
                return text.replace(key, translations[lang_code])
    
    # If not found in our dictionary, return a placeholder translation
    return f"[Translation of '{text}' to {target_language}]"

@mcp.tool()
def get_supported_languages() -> list[str]:
    """Return a list of supported languages for translation"""
    return list(LANGUAGE_CODES.keys())

# Run the MCP server
if __name__ == '__main__':
    mcp.run()