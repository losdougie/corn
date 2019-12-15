import datetime
import time
import hashlib
import os
import subprocess


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
            str(task["py_file"]),
            str(task["args"]),
        ]
    )
    return hashlib.md5(task_string.encode("UTF-8")).hexdigest()


def month_num(month):
    months = {
        "jan": 1,
        "january": 1,
        "feb": 2,
        "february": 2,
        "mar": 3,
        "march": 3,
        "apr": 4,
        "april": 4,
        "may": 5,
        "jun": 6,
        "june": 6,
        "jul": 7,
        "july": 7,
        "aug": 8,
        "august": 8,
        "sep": 9,
        "september": 9,
        "oct": 10,
        "october": 10,
        "nov": 11,
        "november": 11,
        "dec": 12,
        "december": 12,
    }
    if not isinstance(month, str):
        return None
    month = month.strip().lower()
    if month in months:
        return months[month]
    else:
        return None


def weekday_num(weekday):
    weekdays = {
        "mon": 1,
        "monday": 1,
        "tue": 2,
        "tuesday": 2,
        "wed": 3,
        "wednesday": 3,
        "thu": 4,
        "thursday": 4,
        "fri": 5,
        "friday": 5,
        "sat": 6,
        "saturday": 6,
        "sun": 7,
        "sunday": 7,
    }
    if not isinstance(weekday, str):
        return None
    weekday = weekday.strip().lower()
    if weekday in weekdays:
        return weekdays[weekday]
    else:
        return None


def unit_num(unit, time_type):
    limit = {
        "m": {"min": 0, "max": 59},
        "h": {"min": 0, "max": 23},
        "d": {"min": 1, "max": 31},
        "mo": {"min": 1, "max": 12},
        "w": {"min": 0, "max": 7},
    }
    if unit == "min":
        return limit[time_type]["min"]
    if unit == "max":
        return limit[time_type]["max"]
    if unit.isnumeric():
        if limit[time_type]["min"] <= int(unit) <= limit[time_type]["max"]:
            if time_type == "w" and unit == 0:
                unit = (
                    7
                )  # weekday of 0 should be listed as 7 - sunday is 7 in the check
            return int(unit)
    elif time_type == "mo" and month_num(unit) is not None:
        return month_num(unit)
    elif time_type == "w" and weekday_num(unit) is not None:
        return weekday_num(unit)
    return None


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
        weed(
            error_id=line_hash,
            error_text="corn doesn't support cron-style special strings",
        )
        return None
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
    task_string = " ".join(section).strip()
    py_file, args = germinate(task_string, line_hash)
    if py_file is None:
        return None
    task = grow(m, h, d, mo, w, py_file, args, line_hash)
    if task is None:
        return None
    return task


def grow(m, h, d, mo, w, py_file, args, line_hash):
    # standardize the line into a task dictionary
    minute = sprout(m, "m")
    hour = sprout(h, "h")
    day = sprout(d, "d")
    month = sprout(mo, "mo")
    weekday = sprout(w, "w")
    task = {
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "weekday": weekday,
        "py_file": py_file,
        "args": args,
    }
    for unit in task:
        if task[unit] is None:
            weed(
                error_id=line_hash, error_text="Task {} unit is incorrect.".format(unit)
            )
            return None
    # print(task)
    return task


def sprout(time_field, time_type):
    # handle lists - split on commas
    # handle ranges
    # handle divisions
    time_values = []
    if time_field == "*":
        range_start = unit_num("min", time_type)
        range_end = (
            unit_num("max", time_type) + 1
        )  # +1 to get all values in range from range function
        for time_value in range(range_start, range_end):
            time_values.append(time_value)
        return time_values
    units = time_field.split(",")
    for unit in units:
        step = 1
        if "/" in unit:
            range_steps = unit.split("/")
            if len(range_steps) > 2:
                return None
            if range_steps[1].isnumeric():
                step = int(range_steps[1])
                unit = range_steps[0]
                if unit == "*":
                    range_start = unit_num("min", time_type)
                    range_end = unit_num("max", time_type)
                    for time_value in range(range_start, range_end, step):
                        time_values.append(time_value)
                    continue
            else:
                return None
        if "-" in unit:
            unit_range = unit.split("-")
            if len(unit_range) > 2:
                return None
            if unit_range[0].isnumeric() and unit_range[1].isnumeric():
                range_start = int(unit_range[0])
                range_end = (
                    int(unit_range[1]) + 1
                )  # +1 to get all values in range from range function
            else:
                return None
            for time_value in range(range_start, range_end, step):
                time_values.append(time_value)
            continue
        time_value = unit_num(unit, time_type)
        if time_value is None:
            return None
        time_values.append(time_value)
    return time_values


def germinate(task_string, line_hash):
    if task_string == "":
        weed(error_id=line_hash, error_text="No task for line: {}".format(line))
        return None, None
    # find python file
    if ".py" not in task_string:
        weed(
            error_id=line_hash,
            error_text="Python file not found. Python file must end in .py",
        )
        return None, None
    file_args = task_string.split(".py")
    py_file = file_args[0] + ".py"
    py_file = py_file.strip().strip('"')
    base_dir = os.path.dirname(os.path.realpath(__file__))
    if "\\" not in py_file and "/" not in py_file:  # no path, just local file
        py_file = os.path.join(base_dir, py_file)
    elif "\\" in base_dir and "/" in py_file:  # running on windows, fix paths
        py_file = py_file.replace("/", "\\")
    elif "/" in base_dir and "\\" in py_file:  # running on linux, fix paths
        py_file = py_file.replace("\\", "/")
    if py_file[:2] == "./" or py_file[:2] == ".\\":  # local folder
        py_file = os.path.join(base_dir, py_file[2:])
    if not os.path.isfile(py_file):
        weed(error_id=line_hash, error_text="Python file not found: {}".format(py_file))
        return None, None
    if " " in py_file:
        py_file = '"' + py_file + '"'
    if len(file_args) == 1:
        args = ""
    elif len(file_args) == 2:
        args = file_args[1].strip().strip('"')
    else:
        weed(
            error_id=line_hash,
            error_text="Could not determine args for {}".format(py_file),
        )
        return None, None
    return py_file, args


def harvest(schedule, now):
    for task in schedule:
        if ripe(task, now):
            pick(task)


def ripe(task, now):
    if now.minute not in task["minute"]:
        return False
    if now.hour not in task["hour"]:
        return False
    if now.day not in task["day"]:
        return False
    if now.month not in task["month"]:
        return False
    weekday = (
        now.weekday() + 1
    )  # This corrects for datetime to use 1 for Monday and 7 for Sunday
    if weekday not in task["weekday"]:
        return False
    return True


def pick(task):
    # run task as separate process
    # print("Running", task["py_file"], "at {}".format(datetime.datetime.now()))
    # may want to redirect stdout
    print("running {} at {}".format(task["py_file"], datetime.datetime.now()))
    subprocess.Popen(
        " ".join(["python", task["py_file"], task["args"]]).strip(), shell=True
    )


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
    last_run_minute = datetime.datetime.now().minute
    file_hash = ""
    schedule = []
    global errors
    errors = {}
    wait = True

    while True:
        time.sleep(0.2)  # slows loop to only check 5 times a second after waiting
        now = datetime.datetime.now()
        # print("looping at", datetime.datetime.now())
        if wait:
            # waiting for end of the minute
            wait_time = 59 - datetime.datetime.now().second
            # print("waiting for {}s at {}".format(wait_time, datetime.datetime.now()))
            time.sleep(wait_time)
            wait = False
        # start loop at the top of the minute - track last minute
        if last_run_minute < now.minute or (last_run_minute == 59 and now.minute == 0):
            last_run_minute = now.minute
            wait = True
            # print("running at", datetime.datetime.now())

            # check file for changes
            if hash_file(corntab) != file_hash:
                file_hash = hash_file(corntab)
                schedule = plant(corntab)
                print("Scheduled {} tasks".format(len(schedule)))
            harvest(schedule, now)
            weed()


if __name__ == "__main__":
    main()
