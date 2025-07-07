def get_url_vtt_subtitles(subtitles: dict, auto_subtitles: dict) -> str | None:
    """
    Retrieves the URL of the most suitable VTT subtitle file based on language priority.
    """
    priority_langs = [
        # The most popular languages ​​on the Internet (in descending order):
        'en',  # English
        'zh',  # Chinese
        'es',  # Spanish
        'jp',  # Japanese
        'pt',  # Portuguese
        'de',  # German
        'ar',  # Arabic
        'fr',  # French
        'ru',  # Russian
        'ko',  # Korean
        'it',  # Italian
    ]
    if subtitles:
        for lang in priority_langs + list(subtitles):
            if subs := subtitles.get(lang, []):
                return next(s['url'] for s in subs if s['ext'] == 'vtt')

    for lang, subs in auto_subtitles.items():
        if '-orig' in lang:
            return next(s['url'] for s in subs if s['ext'] == 'vtt')


def clean_vtt_text(text: str, is_auto_subtitles: bool) -> str:
    """
    Cleans VTT subtitle text by removing timestamps, empty lines, and HTML tags.

    Args:
        text (str): The raw VTT subtitle text.
        is_auto_subtitles (bool): True if the subtitles are auto-generated, False otherwise.

    Returns:
        str: The cleaned subtitle text.
    """
    lines = text.split('\n')[3:]
    cleaned_lines = [line.strip() for line in lines if line.strip() and '-->' not in line and '</c>' not in line]

    if is_auto_subtitles:
        # autom-subtitles have duplicate lines
        cleaned_lines = cleaned_lines[::2]

    return ' '.join(cleaned_lines)
