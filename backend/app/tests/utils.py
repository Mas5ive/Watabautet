from app import crud
from app.models import Summary, Video
from sqlmodel import Session

VIDEO_LINK = 'v' * 11


def create_video_in_db(
    session: Session,
    link: str = VIDEO_LINK,
    major_language: str = 'ru',
    description: str = 'bla-bla',
    text: str = 'bla-bla',
    category: str = 'comedy',
    title: str = 'wow'
) -> Video:
    """
    Creates a video object in the database using provided data and default values.
    """

    video = crud.create_obj(session=session, obj=Video(
        link=link,
        major_language=major_language,
        description=description,
        text=text,
        category=category,
        title=title
    ))
    return video


def create_summary_in_db(
        session: Session,
        language: str = 'ru',
        size: str = 'small',
        video_link: str = VIDEO_LINK,
        text: str = 'summary text'
) -> Summary:
    """
    Creates a summary object in the database using provided data and default values.
    """

    summary = crud.create_obj(session=session, obj=Summary(
        language=language,
        size=size,
        video_link=video_link,
        text=text
    ))
    return summary


