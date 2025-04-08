from datetime import datetime


def calc_diff_curr_time(date: str, date_format: str = '%Y-%m-%dT%H:%M:%S.%f%z') -> int:
    target_time = datetime.strptime(date, date_format)
    current_time = datetime.now(target_time.tzinfo)
    sec_diff = (current_time - target_time).total_seconds()
    return int(sec_diff)
