import uuid


class _TaskId:
    """
    A base class for generating unique task identifiers using UUID version 5.

    Attributes:
        _namespace (UUID): A predefined UUID namespace used to generate deterministic UUIDs.

    Methods:
        generate(*args: str) -> str:
            Generates a UUID based on the provided arguments using UUIDv5.
    """

    _namespace = uuid.UUID('1bc4e60e-cf57-4d75-a2be-df44aabc1134')

    @classmethod
    def generate(cls, *args: str) -> str:
        """
        Generates a unique task identifier.

        Args:
            *args (str): A variable number of string arguments to create a deterministic UUID.

        Returns:
            str: The generated UUIDv5 string.
        """
        key = '|'.join(args)
        return str(uuid.uuid5(cls._namespace, key))


class TaskIdSummary(_TaskId):
    """
    A class for generating unique summary task identifiers.

    Methods:
        generate(video_link: str, size: str, language: str) -> str:
            Generates a UUID based on video link, size, and language.
    """

    @classmethod
    def generate(cls, *, video_link: str, size: str, language: str) -> str:
        """
        Generates a unique summary task identifier.

        Args:
            video_link (str): The video link to be summarized.
            size (str): The size of the summary.
            language (str): The language of the summary.

        Returns:
            str: The generated UUIDv5 string.
        """
        return super().generate(video_link, size, language)


class TaskIdVideo(_TaskId):
    """
    A class for generating unique video task identifiers.

    Methods:
        generate(link: str) -> str:
            Generates a UUID based on the video link.
    """

    @classmethod
    def generate(cls, *, link: str, major_language: str) -> str:
        """
        Generates a unique video task identifier.

        Args:
            link (str): The video link.
            major_language (str): the main language in the video.

        Returns:
            str: The generated UUIDv5 string.
        """
        return super().generate(link, major_language)
