"""Scoped repository / data-access layer.

No ``execute_sql``, no ``query``, no string-templated query builder is
exposed. Each module returns immutable typed results.
"""
