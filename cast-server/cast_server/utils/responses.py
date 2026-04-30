import json


def toast_header(message: str, toast_type: str = "success") -> str:
    """Build HX-Trigger JSON for toast notifications."""
    return json.dumps({"showToast": {"message": message, "type": toast_type}})
