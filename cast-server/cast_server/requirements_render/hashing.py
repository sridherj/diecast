"""Canonical content hashing for the requirements thin spine.

Deliberately tiny and import-light: Phases 4 and 5 import this WITHOUT importing the parser.
Phase 5 conflict detection MUST use this exact function — never reimplement sha256 elsewhere.
"""
import hashlib


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
