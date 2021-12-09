import json


def load_query_text(text):
    return json.loads(text)


def dump_query_text(query):
    return json.dumps(query, indent=4)


def sanitize_query_text(text):
    """Formats a query text coherently."""
    return dump_query_text(load_query_text(text))


def is_valid_query(text):
    try:
        load_query_text(text)
    except:
        return False
    return True
