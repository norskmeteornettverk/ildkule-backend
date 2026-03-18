from sqlalchemy import case


def desc_nulls_last(column):
    """Return a database-portable DESC ordering with NULL values last."""

    return (
        case((column.is_(None), 1), else_=0),
        column.desc(),
    )
