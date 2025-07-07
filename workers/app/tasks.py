import requests
import yt_dlp
from app import utils
from app.celery import app, logger


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
