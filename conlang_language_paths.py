"""
Centralized language file path management.
All language data is stored in language_data/{language_name}/
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LANGUAGE_DATA_DIR = os.path.join(BASE_DIR, "language_data")


def get_language_dir(language: str) -> str:
    """Get the directory for a specific language, creating it if needed."""
    lang_dir = os.path.join(LANGUAGE_DATA_DIR, language)
    os.makedirs(lang_dir, exist_ok=True)
    return lang_dir


def get_language_file(language: str, filename: str) -> str:
    """Get full path for a language-specific file."""
    return os.path.join(get_language_dir(language), filename)


def list_languages() -> list:
    """List all available languages (subdirectories in language_data)."""
    if not os.path.exists(LANGUAGE_DATA_DIR):
        os.makedirs(LANGUAGE_DATA_DIR, exist_ok=True)
        return []
    return [d for d in os.listdir(LANGUAGE_DATA_DIR) 
            if os.path.isdir(os.path.join(LANGUAGE_DATA_DIR, d))]


# Standard file suffixes for each language (prefixed with {language}_)
FILE_SUFFIXES = {
    "anchors": "_anchors.json",
    "template": "_template.json",
    "build_data": "_build_data.json",
    "dictionary": "_dictionary.json",
    "dict_txt": "_dictionary.txt",
    "suffixes": "_suffixes.json",
    "missing_tags": "_missing_tags.txt",
}


def get_anchors_file(language: str) -> str:
    return get_language_file(language, f"{language}{FILE_SUFFIXES['anchors']}")


def get_template_file(language: str) -> str:
    return get_language_file(language, f"{language}{FILE_SUFFIXES['template']}")


def get_build_data_file(language: str) -> str:
    return get_language_file(language, f"{language}{FILE_SUFFIXES['build_data']}")


def get_dictionary_file(language: str) -> str:
    return get_language_file(language, f"{language}{FILE_SUFFIXES['dictionary']}")


def get_dict_txt_file(language: str) -> str:
    return get_language_file(language, f"{language}{FILE_SUFFIXES['dict_txt']}")


def get_suffixes_file(language: str) -> str:
    return get_language_file(language, f"{language}{FILE_SUFFIXES['suffixes']}")


def get_missing_tags_file(language: str) -> str:
    return get_language_file(language, f"{language}{FILE_SUFFIXES['missing_tags']}")
