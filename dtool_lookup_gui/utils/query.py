import json


def load_query_text(text):
    return json.loads(text)


def dump_single_line_query_text(query):
    return json.dumps(query)


def dump_multi_line_query_text(query):
    return json.dumps(query, indent=4)


def single_line_sanitize_query_text(text):
    """Formats a query text coherently."""
    return dump_single_line_query_text(load_query_text(text))


def multi_line_sanitize_query_text(text):
    """Formats a query text coherently."""
    return dump_multi_line_query_text(load_query_text(text))


def is_valid_query(text):
    try:
        load_query_text(text)
    except:
        return False
    return True
