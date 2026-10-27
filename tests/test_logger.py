from app.logger import get_logger


def test_get_logger_does_not_add_duplicate_handlers():
    first = get_logger("test_dup")
    count = len(first.handlers)
    second = get_logger("test_dup")
    assert second is first
    assert len(second.handlers) == count