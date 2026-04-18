import os
from typing import TYPE_CHECKING

import requests
from google.genai import Client, errors, types
from yt_dlp.utils import DownloadError
from yt_dlp.YoutubeDL import YoutubeDL

from app import utils
from app.celery import app, logger
from app.exceptions import ImpossibleTaskError, non_retriable_google_api_errors, retriable_google_api_errors

if TYPE_CHECKING:
    from yt_dlp import _Params


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

    ydl_opts: _Params = {
        'quiet': True,
        'cachedir': None,

        # Search only for formats that have already been merged.
        # This will eliminate the need for ffmpeg checking and remove the warning.
        'format': 'b',
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
                    raise ImpossibleTaskError(f'It is impossible to work with video {video['link']}. Reason: {msg}')
            else:
                logger.warning(f'DownloadError for video {video['link']}. Retrying... Error: {e}')
                raise

    subtitles = info.get('subtitles', {})
    auto_subtitles = info.get('automatic_captions', {})

    all_subtitles = (subtitles, auto_subtitles)
    if not any(all_subtitles):
        raise ImpossibleTaskError(f'The video {video['link']} has no subtitles')

    subs_url = utils.get_url_vtt_subtitles(*all_subtitles)
    if not subs_url:
        raise ImpossibleTaskError(f'The video {video['link']} has no VTT-subtitles')

    try:
        response = requests.get(subs_url, timeout=30)
        response.raise_for_status()  # HTTP (4xx, 5xx)
    except requests.exceptions.RequestException as e:
        logger.warning(f'RequestException for subtitles on video {video['link']}. Retrying... Error: {e}')
        raise

    video_text = utils.clean_vtt_text(response.text, is_auto_subtitles=bool(auto_subtitles))

    result = {
        'title': info.get('title') or 'no title',
        'description': (info.get('description') or 'no description').replace('\n', ''),
        'category': (info.get('categories') or ['no category'])[0],
        'text': video_text
    }
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
        except errors.APIError as e:
            if e.code in retriable_google_api_errors:
                logger.warning(f'Google API error for video {video['link']}. Retrying... Error: {e}')
                raise retriable_google_api_errors[e.code](e)
            elif e.code in non_retriable_google_api_errors:
                raise ImpossibleTaskError(f'Google API error for video {video['link']}. Error: {e}')
            else:
                logger.error(f'Unexpected Google API error for video {video['link']}. Error: {e}')
                raise
        except ValueError as e:
            raise ImpossibleTaskError(
                f'Content generation from video {video['link']} failed, likely due to safety filters. Reason: {e}'
            )

    return {
        'video_link': video['link'],
        'size': summary['size'],
        'language': summary['language'],
        'text': text,
    }
