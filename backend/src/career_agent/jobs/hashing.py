import hashlib
import re


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def sha256_text(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def manual_source_id(company: str, title: str) -> str:
    identity = f"{normalize_text(company).lower()}|{normalize_text(title).lower()}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
