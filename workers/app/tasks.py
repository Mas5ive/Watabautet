import os
from typing import TYPE_CHECKING

import structlog
from google.genai import Client, errors, types
from yt_dlp.utils import DownloadError
from yt_dlp.YoutubeDL import YoutubeDL

from app.celery import StructlogYTDLPLogger, app
from app.exceptions import ImpossibleTaskError, non_retriable_google_api_errors, retriable_google_api_errors
from app.subtitle import Subtitle

if TYPE_CHECKING:
    from yt_dlp import _Params

logger = structlog.get_logger()


@app.task
def get_video_data(video: dict) -> dict:
    """
    Retrieves video data, including title, description, category, and cleaned VTT subtitles.
    The task will retry if a DownloadError or RequestException occurs.
    Raises:
        ImpossibleTaskError: If the video is unavailable, age-restricted, has no subtitles,
                               or no VTT subtitles are found.
    Returns:
        dict: A dictionary containing the video's title, description, category, and cleaned subtitle text.
    """
    log = logger.bind(video_link=video['link'])
    log.info('received')

    ydl_opts: _Params = {
        'quiet': True,
        'cachedir': None,
        # Search only for formats that have already been merged.
        # This will eliminate the need for ffmpeg checking and remove the warning.
        'format': 'b',
        'logger': StructlogYTDLPLogger(),

        # Completely disable any internal tries by yt-dlp
        'retries': 0,
        'extractor_retries': 0,
        'fragment_retries': 0,
        'file_access_retries': 0,
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info('https://youtu.be/' + f'{video['link']}', download=False)
        except DownloadError as e:
            for msg in (
                'Private video',
                'Age-restricted',
                'Video unavailable',
                'policy on hate speech',
                'This video is not available',
                'The uploader has not made this video available in your country',
            ):
                if msg in (e.msg or ''):
                    log.info('rejected', reason='impossible_task', details=e.msg)
                    raise ImpossibleTaskError(f'Unfortunately, this video cannot be processed. Reason: {msg}')
            else:
                raise

    if urls_subtitles := info.get('subtitles', {}):
        subtitle = Subtitle(tracks_by_lang=urls_subtitles, is_auto=False)
    elif urls_auto_subtitles := info.get('automatic_captions', {}):
        subtitle = Subtitle(tracks_by_lang=urls_auto_subtitles, is_auto=True)
    else:
        log.info('rejected', reason='impossible_task', details='no_subtitles')
        raise ImpossibleTaskError('The video has no subtitles.')

    video_text = subtitle.get()  # A `requests.exceptions.RequestException` exception may occur here

    if not video_text:
        log.info('rejected', reason='impossible_task', details='no_vtt_subtitles')
        raise ImpossibleTaskError('The video has no VTT-subtitles.')

    result = {
        'title': info.get('title') or 'no title',
        'description': (info.get('description') or 'no description').replace('\n', ''),
        'category': (info.get('categories') or ['no category'])[0],
        'text': video_text
    }
    log.info('succeeded')
    return result


@app.task
def make_summary(summary: dict, video: dict) -> dict:
    """
    Generates a summary of a video using the Google Generative AI model.
    The task will retry if a Google API exception occurs.
    Raises:
        ImpossibleTaskError: If the video is too long to be summarized
                                or content generation fails due to safety filters.
    Returns:
        dict: A dictionary containing the video link, summary size, language, and the generated summary text.
    """
    log = logger.bind(video_link=video['link'])
    log.info('received')

    size_instructions = {
        'small': ('Create a very brief summary (TL;DR). It should be 1-2 sentences long and reflect the most important '
                  'point or key takeaway from the video.'),
        'medium': ('Create a standard summary in one solid paragraph (approximately 4-6 sentences). Include the main '
                   'talking points and key points discussed in the video.'),
        'large': ('Create a detailed and structured summary. Present it as a list of all the key points. Each point '
                  'should be expanded on in detail (2-3 sentences per point) to give a complete overview of '
                  'the content of the video')
    }

    prompt = f"""
        # ROLE
        You are an AI assistant, an expert in analyzing and summarizing textual information.

        # TASK
        Your job is to analyze subtitles from videos and create a quality summary based on them.

        # INSTRUCTIONS
        - Language of the final summary: {summary['language']}.
        - Style and size of the resume: {size_instructions[summary['size']]}.
        - Start your text right away with a summary without any preface.
        - Base your summary EXCLUSIVELY on the information in the subtitles provided below.
          Do not add anything of your own.

        # SOURCE DATA
        - Video title: {video['title']}.
        - Video category: {video['category']}.
        - Video description: {video['description']}.

        ## SUBTITLES
        ---
        {video['text']}
        ---
    """

    request_timeout = int(os.getenv('GOOGLE_API_TIMEOUT_SEC', 120))
    with Client(http_options=types.HttpOptions(timeout=request_timeout * 1000)) as client:
        try:
            response = client.models.generate_content(model=os.environ["GOOGLE_LLM"], contents=prompt)
            text = response.text
        # An error httpx.ConnectError may also occur here
        except errors.APIError as e:
            if e.code in retriable_google_api_errors:
                sub_e = retriable_google_api_errors[e.code](code=e.code, response_json=e.details, response=e.response)
                log.warning('rejected', reason='google_api_error', details=sub_e)
                raise sub_e
            elif e.code in non_retriable_google_api_errors:
                sub_e = non_retriable_google_api_errors[e.code](
                    code=e.code, response_json=e.details, response=e.response
                )
                log.info('rejected', reason='impossible_task', details=sub_e)
                raise ImpossibleTaskError('Google API error for the video.')
            else:
                raise
        except ValueError as e:
            log.info('rejected', reason='impossible_task', details=str(e))
            raise ImpossibleTaskError('Content generation from the video failed, likely due to safety filters.')

    log.info('succeeded')
    return {
        'video_link': video['link'],
        'size': summary['size'],
        'language': summary['language'],
        'text': text,
    }
