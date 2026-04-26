"""AO Radar private DB-ops Lambda package.

Canonical deployed path for migrations and seed/reset. Invoked through the
Terraform-managed ``ao-radar-db-ops`` Lambda; never connected to API
Gateway. Operations: ``migrate``, ``seed``, ``seed`` with ``reset = true``.
"""

__version__ = "0.1.0"
