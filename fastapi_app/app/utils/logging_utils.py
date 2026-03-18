import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


_CONFIGURED = False


def configure_logging(log_level: str = "INFO", log_file: str | None = None) -> logging.Logger:
    """Configure process-wide logging once and return the app logger."""

    global _CONFIGURED

    level = getattr(logging, str(log_level).upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    if not _CONFIGURED:
        has_stream_handler = any(
            isinstance(handler, logging.StreamHandler)
            and not isinstance(handler, logging.FileHandler)
            for handler in root_logger.handlers
        )
        if not has_stream_handler:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(level)
            stream_handler.setFormatter(formatter)
            root_logger.addHandler(stream_handler)

        if log_file:
            log_path = Path(log_file).expanduser()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            resolved_log_path = str(log_path.resolve())
            has_file_handler = any(
                isinstance(handler, logging.FileHandler)
                and getattr(handler, "baseFilename", None) == resolved_log_path
                for handler in root_logger.handlers
            )
            if not has_file_handler:
                file_handler = RotatingFileHandler(
                    resolved_log_path,
                    maxBytes=5_000_000,
                    backupCount=3,
                    encoding="utf-8",
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)

        _CONFIGURED = True

    app_logger = logging.getLogger("ildkule.fastapi")
    app_logger.setLevel(level)
    return app_logger
