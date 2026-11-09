from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable


CATALOG = {
    "PANEL-WHITE-18": {"name": "Płyta biała 18 mm", "unit_net": Decimal("55.00")},
    "EDGE-OAK-22": {"name": "Obrzeże dąb 22 mm", "unit_net": Decimal("18.00")},
    "HANDLE-BLACK-160": {"name": "Uchwyt czarny 160 mm", "unit_net": Decimal("24.50")},
}


def _money(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def process_order(payload: dict[str, Any], seen_source_ids: Iterable[str] | None = None) -> dict[str, Any]:
    """Validate and match an order without guessing unknown catalogue identities."""
    if not isinstance(payload, dict):
        return {
            "status": "invalid",
            "errors": ["payload_must_be_an_object"],
            "net_total": None,
            "gross_total": None,
        }

    source_id = payload.get("source_id")
    if source_id is not None:
        if not isinstance(source_id, str) or not source_id.strip():
            return {
                "status": "invalid",
                "errors": ["source_id_must_be_a_non_empty_string"],
                "net_total": None,
                "gross_total": None,
            }
        source_id = source_id.strip()
    if source_id and source_id in set(seen_source_ids or []):
        return {"status": "duplicate", "reason": "source_id_already_processed", "source_id": source_id}

    customer = str(payload.get("customer", "")).strip()
    lines = payload.get("lines")
    if not customer or not isinstance(lines, list) or not lines:
        return {
            "status": "invalid",
            "errors": ["customer_and_non_empty_lines_are_required"],
            "net_total": None,
            "gross_total": None,
        }

    matched: list[dict[str, Any]] = []
    review_items: list[dict[str, Any]] = []
    net_total = Decimal("0")

    for index, line in enumerate(lines, start=1):
        if not isinstance(line, dict):
            review_items.append({"line": index, "reason": "invalid_line"})
            continue
        sku = str(line.get("sku", "")).strip().upper()
        quantity = line.get("quantity")
        product = CATALOG.get(sku)
        if product is None:
            review_items.append({"line": index, "sku": sku, "reason": "unknown_sku"})
            continue
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1 or quantity > 10_000:
            review_items.append({"line": index, "sku": sku, "reason": "invalid_quantity"})
            continue

        line_net = product["unit_net"] * quantity
        net_total += line_net
        matched.append(
            {
                "line": index,
                "sku": sku,
                "name": product["name"],
                "quantity": quantity,
                "unit_net": _money(product["unit_net"]),
                "line_net": _money(line_net),
            }
        )

    if review_items:
        return {
            "status": "needs_review",
            "customer": customer,
            "matched_lines": matched,
            "review_items": review_items,
            "net_total": None,
            "gross_total": None,
        }

    return {
        "status": "ready",
        "customer": customer,
        "source_id": source_id,
        "matched_lines": matched,
        "review_items": [],
        "net_total": _money(net_total),
        "gross_total": _money(net_total * Decimal("1.23")),
    }
