import datetime
import time
import hashlib


def hash_file(file):
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def hash_task(task):
    task_string = "".join(
        [
            str(task["minute"]),
            str(task["hour"]),
            str(task["day"]),
            str(task["month"]),
            str(task["weekday"]),
            str(task["task"]),
        ]
    )
    return hashlib.md5(task_string.encode("UTF-8")).hexdigest()


def plant(file):
    schedule = []
    task_hashes = []
    print("Reading file: {}".format(file))
    with open(file, "r") as f:
        for line in f:
            line = line.strip()
            if line == "":
                continue
            if line[:1] == "#":
                continue
            task = sow(line)
            if task is None:
                continue
            # check that tasks do not repeat - get hash after processed
            task_hash = hash_task(task)
            if task_hash in task_hashes:
                continue
            task_hashes.append(task_hash)
            schedule.append(task)
    return schedule


def sow(line):
    # check if line is an existing error - get line hash first
    line_hash = hashlib.md5(line.encode("UTF-8")).hexdigest()
    if line_hash in errors:
        return None
    if line[:1] == "@":
        weed(error_id=line_hash, error_text="corn doesn't support cron-style special strings")
        return None
    # standardize the line into a task dictionary
    minute = []
    hour = []
    day = []
    month = []
    weekday = []
    task_text = ""
    # break up line into sections - split on space and tab
    line = line.replace("\t", " ")
    while "  " in line:
        line.replace("  ", " ")
    section = line.split(" ")
    if len(section) < 6:
        weed(error_id=line_hash, error_text="Invalid line: {}".format(line))
        return None
    # read first five sections - minute, hour, day, month, weekday
    m = section.pop(0)
    h = section.pop(0)
    d = section.pop(0)
    mo = section.pop(0)
    w = section.pop(0)
    tt = " ".join(section).strip()
    if tt == "":
        weed(error_id=line_hash, error_text="No task for line: {}".format(line))
        return None
    task_text = tt
    # handle ranges
    # handle divisions
    # handle lists - split on commas
    if m != "*":
        if m.isnumeric() and 0 < int(m) < 59:
            minute.append(int(m))
    if h != "*":
        if h.isnumeric() and 0 < int(h) < 60:
            hour.append(int(h))
    if d != "*":
        if d.isnumeric() and 1 < int(d) < 31:
            day.append(int(d))
    if mo != "*":
        if mo.isnumeric() and 1 < int(mo) < 12:
            month.append(int(mo))
    if w != "*":
        week_names = {
            "mon": 1,
            "tue": 2,
            "wed": 3,
            "thu": 4,
            "fri": 5,
            "sat": 6,
            "sun": 7,
        }
        if w.isnumeric() and 0 < w < 7:
            if w == 0:
                w = 7  # weekday of 0 should be listed as 7 - sunday is 7 in the check
            weekday.append(int(w))
        elif w.lower() in week_names:  # (3 letters or full name - case insensitive)
            weekday.append(week_names[w.lower()])
    task = {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "weekday": weekday,
        "task": task_text,
    }
    return task


def harvest(schedule, now):
    for task in schedule:
        if ripe(task, now):
            pick(task)


def ripe(task, now):
    if task["minute"] != [] and now.minute not in task["minute"]:
        return False
    if task["hour"] != [] and now.hour not in task["hour"]:
        return False
    if task["day"] != [] and now.day not in task["day"]:
        return False
    if task["month"] != [] and now.month not in task["month"]:
        return False
    weekday = (
        now.weekday() + 1
    )  # This corrects for datetime to use 1 for Monday and 7 for Sunday
    if task["weekday"] != [] and weekday not in task["weekday"]:
        return False
    return True


def pick(task):
    # run task as separate process
    print(task["task"], "at {}".format(datetime.datetime.now()))

def weed(error_id=None, error_text=None):
    # global error handling and prints errors only once.
    global errors
    if error_id is not None:
        if error_id not in errors:
            errors[error_id] = error_text
    else:
        for error in errors:
            if errors[error] is not None:
                print(errors[error])
                errors[error] = None



def main():
    corntab = "corntab.txt"
    last_run_minute = datetime.datetime.now().minute - 1
    file_hash = ""
    schedule = []
    global errors
    errors = {}

    while True:
        now = datetime.datetime.now()
        # start loop at the top of the minute - track last minute
        if last_run_minute < now.minute or (last_run_minute == 60 and now.minute == 0):
            last_run_minute = now.minute
            wait = True

            # check file for changes
            if hash_file(corntab) != file_hash:
                file_hash = hash_file(corntab)
                schedule = plant(corntab)
                print("Scheduled {} tasks".format(len(schedule)))
            harvest(schedule, now)
            weed()

        if wait:
            # waiting for close to minute
            time.sleep(59 - datetime.datetime.now().second)
            wait = False
        time.sleep(0.2)  # slows loop to only check 5 times a second after waiting


def test():
    print("ok")


if __name__ == "__main__":
    main()
