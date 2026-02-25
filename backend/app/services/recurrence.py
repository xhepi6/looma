from datetime import datetime, timedelta, timezone
import calendar


DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def compute_next_due_date(
    current_due: datetime | None,
    recurrence_type: str,
    recurrence_days: list[str] | None = None,
) -> datetime:
    if current_due is None:
        base = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
    else:
        base = current_due

    if recurrence_type == "daily":
        return _noon_utc(base + timedelta(days=1))

    if recurrence_type == "weekly":
        return _noon_utc(base + timedelta(days=7))

    if recurrence_type == "monthly":
        return _noon_utc(_add_month(base))

    if recurrence_type == "weekdays":
        return _noon_utc(_next_weekday(base))

    if recurrence_type == "custom" and recurrence_days:
        return _noon_utc(_next_custom_day(base, recurrence_days))

    # Fallback: tomorrow
    return _noon_utc(base + timedelta(days=1))


def _noon_utc(dt: datetime) -> datetime:
    return dt.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)


def _add_month(dt: datetime) -> datetime:
    year = dt.year + (dt.month // 12)
    month = (dt.month % 12) + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _next_weekday(dt: datetime) -> datetime:
    next_day = dt + timedelta(days=1)
    while next_day.weekday() >= 5:  # 5=Sat, 6=Sun
        next_day += timedelta(days=1)
    return next_day


def _next_custom_day(dt: datetime, days: list[str]) -> datetime:
    target_weekdays = {DAY_NAMES.index(d.lower()) for d in days if d.lower() in DAY_NAMES}
    if not target_weekdays:
        return dt + timedelta(days=1)
    next_day = dt + timedelta(days=1)
    for _ in range(7):
        if next_day.weekday() in target_weekdays:
            return next_day
        next_day += timedelta(days=1)
    return dt + timedelta(days=1)
