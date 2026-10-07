"""Pagination utilities and helpers."""


def get_pagination_offset(page: int, page_size: int) -> int:
    """Calculate database query offset from 1-indexed page."""
    safe_page = max(page, 1)
    safe_page_size = max(min(page_size, 100), 1)
    return (safe_page - 1) * safe_page_size


def calculate_total_pages(total_items: int, page_size: int) -> int:
    """Calculate total pages."""
    if total_items <= 0:
        return 1
    safe_page_size = max(page_size, 1)
    return (total_items + safe_page_size - 1) // safe_page_size
