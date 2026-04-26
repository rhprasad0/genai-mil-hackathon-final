"""AO Radar synthetic seed package.

Contents (per docs/synthetic-data-implementation-plan.md sections 9-13):

* ``cards/`` — twelve voucher YAML story cards (sources of truth).
* ``travelers.yaml``, ``prior_summaries.yaml``, ``citations.yaml``,
  ``coverage_map.yaml``, ``refusal_seeds.yaml`` — supporting fixtures.
* ``generators/`` — deterministic in-memory row builders.
* ``validators/`` — pure validators that fail closed before any DB write.
* ``validate.py`` / ``snapshot.py`` / ``load.py`` / ``reset.py`` — CLI entry
  points.

Every value in this package is synthetic. No real names, vendors, places,
units, GTCC data, bank routing data, real LOAs, or real policy text appears
anywhere in the seed.
"""
