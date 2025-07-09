import os

import google.generativeai as genai
import requests
import yt_dlp
from app import utils
from app.celery import app, logger
from google.api_core import exceptions as google_exceptions


class ImpossibleTaskError(Exception):
    """
    Custom exception raised when a task encounters an impossible state or
    a condition that prevents it from completing successfully, even after retries.
    """
    pass


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

    ydl_opts = {
        'quiet': True,
        'cachedir': False,

        # Search only for formats that have already been merged.
        # This will eliminate the need for ffmpeg checking and remove the warning.
        'format': 'b',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info('https://youtu.be/' + f'{video['link']}', download=False)
        except yt_dlp.utils.DownloadError as e:
            for msg in (
                'Private video',
                'Age-restricted',
                'Video unavailable',
                'policy on hate speech',
                'This video is not available',
                'The uploader has not made this video available in your country',
            ):
                if msg in e.msg:
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
        'title': info['title'] or 'no title',
        'description': info['description'].replace('\n', '') or 'no description',
        'category': info['categories'][0] if info['categories'] else 'no category',
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
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(os.environ["GOOGLE_LLM"])
    request_timeout = int(os.getenv('GOOGLE_API_TIMEOUT_SEC', 120))

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
    try:
        response = model.generate_content(prompt, request_options={'timeout': request_timeout})
        text = response.text
    except (
        google_exceptions.ResourceExhausted,  # [429] # You've exceeded the rate limit.
        google_exceptions.ServiceUnavailable,  # [503] # The service may be temporarily overloaded or down.
        google_exceptions.DeadlineExceeded,  # [504] Your prompt (or context) is too large to be processed in time.
    ) as e:
        logger.warning(f'Google API error for video {video['link']}. Retrying... Error: {e}')
        raise
    except google_exceptions.InternalServerError as e:  # [500] Your input context is too long.
        raise ImpossibleTaskError(f'The video {video['link']} is too long to be summarized. Reason: {e}')
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
