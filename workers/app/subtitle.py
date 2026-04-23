import abc

import requests


class SubtitleProcessor(abc.ABC):
    """
    A base abstract class for processing and cleaning subtitle text.
    """

    @staticmethod
    def fetch_text(url: str) -> str:
        """
        Retrieves the text content of the subtitles from the specified URL.

        Args:
            url (str): The URL of the subtitle file.

        Returns:
            str: The contents of the file as a string.

        Raises:
            requests.exceptions.HTTPError: If the request ended with an error.
        """
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    @staticmethod
    @abc.abstractmethod
    def clean_text(text: str, is_auto: bool) -> str:
        """
        An abstract method for removing metadata from subtitle text.

        Args:
            text (str): Original subtitle text.
            is_auto (bool): A flag indicating whether the subtitles were generated automatically.
        """
        pass


class VTTProcessor(SubtitleProcessor):
    """
    A processor for handling WebVTT (.vtt) subtitles.
    """

    @staticmethod
    def clean_text(text: str, is_auto: bool) -> str:
        """
        Removes timestamps, formatting tags, and headers from VTT text.

        Args:
            text (str): Source VTT text.
            is_auto (bool): If True, filters out duplicate rows that are typically generated automatically.

        Returns:
            str: The cleaned-up text, combined into a single line.
        """
        lines = text.splitlines()[3:]
        cleaned_lines = [line.strip() for line in lines if line.strip() and '-->' not in line and '</c>' not in line]

        if is_auto:
            cleaned_lines = cleaned_lines[::2]  # Removes duplicates
        return ' '.join(cleaned_lines)


class Subtitle:
    """
    A class for managing the search, loading, and processing of subtitle tracks.

    Attributes:
        PRIORITY_LANGS (list): List of preferred languages for subtitles.
        processors (dict): A mapping of file extensions to their respective SubtitleProcessor classes.
    """
    PRIORITY_LANGS = [
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

    processors = {
        'vtt': VTTProcessor,
    }

    def __init__(self, tracks_by_lang: dict[str, list[dict[str, str]]], is_auto: bool) -> None:
        """
        Initializes the subtitle object.

        Args:
            tracks_by_lang (dict): A list of tracks grouped by language code.
            is_auto (bool): Automatic subtitle mode.
        """
        self.tracks_by_lang = tracks_by_lang
        self.is_auto = is_auto

    def get(self, text_format: str = 'vtt') -> str | None:
        """
        It finds the most appropriate pattern, applies it, and returns the cleaned text.

        Args:
            text_format (str): Desired subtitle file format (extension). The default is vtt.

        Returns:
            str | None: The processed subtitle text, or None if no matching track was found.
        """
        target_tracks = []
        url = None

        if self.is_auto:
            for lang, tracks in self.tracks_by_lang.items():
                if '-orig' in lang:
                    target_tracks = tracks
                    break
        else:
            all_langs = self.PRIORITY_LANGS + list(self.tracks_by_lang.keys())
            for lang in all_langs:
                if lang in self.tracks_by_lang:
                    target_tracks = self.tracks_by_lang[lang]
                    break

        for track in target_tracks:
            if track.get('ext') == text_format:
                url = track.get('url')
                break

        if not url:
            return None

        processor = self.processors[text_format]
        raw_text = processor.fetch_text(url)
        result = processor.clean_text(raw_text, self.is_auto)
        return result
