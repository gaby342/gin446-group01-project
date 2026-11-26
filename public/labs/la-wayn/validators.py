"""Server-side validation for user supplied form and JSON data."""
import re


class ValidationError(ValueError):
    pass


def text(value, label, minimum=1, maximum=120):
    value = str(value or "").strip()
    if not minimum <= len(value) <= maximum:
        raise ValidationError(f"{label} must be between {minimum} and {maximum} characters.")
    return value


def email(value):
    value = text(value, "Email", 5, 254).lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValidationError("Enter a valid email address.")
    return value


def password(value):
    value = str(value or "")
    if len(value) < 8 or len(value) > 128:
        raise ValidationError("Password must be between 8 and 128 characters.")
    return value


def coordinates(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        raise ValidationError("Choose a valid map location.")
    if not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise ValidationError("Choose a valid map location.")
    return lat, lon


def radius(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Choose a radius between 500 m and 20 km.")
    if not 500 <= value <= 20000:
        raise ValidationError("Choose a radius between 500 m and 20 km.")
    return value


def choices(value, allowed, label):
    if not isinstance(value, list):
        value = [] if not value else [value]
    result = list(dict.fromkeys(str(item) for item in value))
    if any(item not in allowed for item in result):
        raise ValidationError(f"Choose valid {label} options.")
    return result


def rating(value):
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Choose a rating from 1 to 5.")
    if not 1 <= value <= 5:
        raise ValidationError("Choose a rating from 1 to 5.")
    return value
