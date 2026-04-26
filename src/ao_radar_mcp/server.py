"""MCP-shaped server with declarative tool registration.

Sources of truth:
  - docs/spec.md section 4.5 (tool catalog).
  - docs/application-implementation-plan.md section 6 (FastMCP wiring,
    ``tools/list`` matches catalog exactly).

FastMCP is the intended runtime adapter, but it is not pip-installable in
the hackathon sandbox.  This module therefore implements the small surface
of MCP that the application actually needs (``initialize``, ``tools/list``,
``tools/call``) with declarative tool registration.  Swapping to a real
FastMCP server later is a one-line change inside ``MCPServer.__init__``;
the tool modules expose ``TOOL_NAME``, ``description``, ``INPUT_SCHEMA``,
and a ``handler`` callable that the registration helper consumes verbatim.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

from .safety.refusal import REFUSAL_REASONS, get_boundary_reminder
from .tools import (
    analyze_voucher_story,
    draft_return_comment,
    export_review_brief,
    get_audit_trail,
    get_external_anomaly_signals,
    get_policy_citation,
    get_policy_citations,
    get_traveler_profile,
    get_voucher_packet,
    list_prior_voucher_summaries,
    list_vouchers,
    mark_finding_reviewed,
    prepare_ao_review_brief,
    record_ao_feedback,
    record_ao_note,
    request_traveler_clarification,
    set_voucher_review_status,
)


@dataclass
class ToolRegistration:
    """Declarative record for a single MCP tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]


@dataclass
class MCPServer:
    """Minimal MCP-shaped server."""

    server_name: str
    server_version: str
    tools: dict[str, ToolRegistration] = field(default_factory=dict)
    protocol_version: str = "2024-11-05"

    def register(self, registration: ToolRegistration) -> None:
        if registration.name in self.tools:
            raise ValueError(f"tool already registered: {registration.name}")
        self.tools[registration.name] = registration

    def register_module(self, module: Any) -> None:
        """Register a tool module that exports the canonical attributes."""

        registration = ToolRegistration(
            name=getattr(module, "TOOL_NAME"),
            description=getattr(module, "description"),
            input_schema=getattr(module, "INPUT_SCHEMA"),
            handler=getattr(module, "handler"),
        )
        self.register(registration)

    # ------------------------------------------------------------------
    # MCP method dispatch
    # ------------------------------------------------------------------

    def initialize(self) -> dict[str, Any]:
        return {
            "protocolVersion": self.protocol_version,
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
            },
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "boundary_reminder": get_boundary_reminder(),
        }

    def list_tools(self) -> dict[str, Any]:
        tools: list[dict[str, Any]] = []
        for name in TOOL_NAMES_IN_SPEC_ORDER:
            tool = self.tools[name]
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.input_schema,
                }
            )
        return {"tools": tools}

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        if name not in self.tools:
            raise UnknownToolError(name)
        registration = self.tools[name]
        result = registration.handler(arguments or {})
        return {
            "content": result if isinstance(result, list) else [_to_text_content(result)],
            "structuredContent": result if isinstance(result, dict) else None,
        }


class UnknownToolError(LookupError):
    """Raised by ``MCPServer.call_tool`` when the tool name is unknown."""


def _to_text_content(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {"type": "json", "json": value}
    return {"type": "text", "text": str(value)}


# Spec section 4.5 catalog in canonical order.  ``tools/list`` must equal this
# exactly.  Adding or removing entries here is treated as a contract change
# and a test failure (see tests/contract/test_tools_list.py).
TOOL_NAMES_IN_SPEC_ORDER: tuple[str, ...] = (
    "list_vouchers_awaiting_action",
    "get_voucher_packet",
    "get_traveler_profile",
    "list_prior_voucher_summaries",
    "get_external_anomaly_signals",
    "analyze_voucher_story",
    "get_policy_citation",
    "get_policy_citations",
    "prepare_ao_review_brief",
    "export_review_brief",
    "record_ao_note",
    "mark_finding_reviewed",
    "record_ao_feedback",
    "draft_return_comment",
    "request_traveler_clarification",
    "set_voucher_review_status",
    "get_audit_trail",
)


def build_server(server_name: str, server_version: str) -> MCPServer:
    """Construct a fully-registered MCP server instance."""

    server = MCPServer(server_name=server_name, server_version=server_version)
    modules = (
        list_vouchers,
        get_voucher_packet,
        get_traveler_profile,
        list_prior_voucher_summaries,
        get_external_anomaly_signals,
        analyze_voucher_story,
        get_policy_citation,
        get_policy_citations,
        prepare_ao_review_brief,
        export_review_brief,
        record_ao_note,
        mark_finding_reviewed,
        record_ao_feedback,
        draft_return_comment,
        request_traveler_clarification,
        set_voucher_review_status,
        get_audit_trail,
    )
    for module in modules:
        server.register_module(module)
    # Sanity: registered names match the catalog in spec order.
    if tuple(server.tools) != TOOL_NAMES_IN_SPEC_ORDER:
        # Re-sort by spec catalog so iteration order matches.
        ordered = {name: server.tools[name] for name in TOOL_NAMES_IN_SPEC_ORDER}
        server.tools = ordered
    _assert_no_generic_tools(server.tools.keys())
    return server


_GENERIC_DATA_ACCESS_NEEDLES: tuple[str, ...] = (
    "query_database",
    "execute_sql",
    "run_query",
    "read_file",
    "list_dir",
    "download_file",
    "fetch_url",
    "http_get",
    "eval",
    "shell",
    "admin_",
)


def _assert_no_generic_tools(names: Iterable[str]) -> None:
    for name in names:
        lowered = name.lower()
        for needle in _GENERIC_DATA_ACCESS_NEEDLES:
            if needle in lowered:
                raise RuntimeError(
                    f"refusing to register generic-data-access tool name: {name!r}"
                )


__all__ = [
    "MCPServer",
    "ToolRegistration",
    "TOOL_NAMES_IN_SPEC_ORDER",
    "UnknownToolError",
    "build_server",
    "REFUSAL_REASONS",
]
