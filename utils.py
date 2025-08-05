from flask import url_for


def calculate_page_link(page: int, query_string: str) -> str:
    """Generate pagination link with query parameters"""
    href = f"{url_for('index')}?current_page={page}"
    if query_string:
        href += f"&{query_string}"
    return href


def build_query_string(request_args: dict) -> str:
    """Build query string excluding current_page parameter"""
    query_params = []
    for key, value in request_args.items():
        if key != "current_page" and value:
            query_params.append(f"{key}={value}")
    return "&".join(query_params)
