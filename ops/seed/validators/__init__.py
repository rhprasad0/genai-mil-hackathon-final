"""Pure validators run before any DB write.

Validator order (synthetic-data plan section 13):
1. ``cards.py`` parses every YAML against the Pydantic card schema.
2. ``synthetic_markers.py`` checks display names, vendor labels, LOA prefixes.
3. ``blocked_status.py`` mirrors schema plan section 6.4 blocklist.
4. ``unsafe_wording.py`` runs the context-aware narrative check.
5. ``authority_boundary.py`` asserts boundary text equals the canonical string.
6. ``signal_keys.py`` enforces deterministic signal_key uniqueness.
7. After generation: ``fk_and_volume.py``, ``coverage.py``, ``audit_invariants.py``.
"""
