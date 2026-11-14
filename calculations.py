from __future__ import annotations


def as_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def calculate_costing(inputs: dict[str, object]) -> tuple[dict[str, float | None], list[str]]:
    missing: list[str] = []
    direct_cost = as_number(inputs.get("direct_cost"))
    indirect_cost = as_number(inputs.get("indirect_cost"))
    annual_transactions = as_number(inputs.get("annual_transactions"))
    current_fee = as_number(inputs.get("current_fee")) or 0
    proposed_fee = as_number(inputs.get("proposed_fee")) or 0
    third_party_fee = as_number(inputs.get("third_party_fee")) or 0
    other_charges = as_number(inputs.get("other_mandatory_charges")) or 0

    if direct_cost is None:
        missing.append("direct_cost")
    if indirect_cost is None:
        missing.append("indirect_cost")
    if annual_transactions is None:
        missing.append("annual_transactions")

    if any(v is not None and v < 0 for v in [direct_cost, indirect_cost, annual_transactions, current_fee, proposed_fee, third_party_fee, other_charges]):
        missing.append("negative_values_not_allowed")

    total_cost = None if direct_cost is None or indirect_cost is None else direct_cost + indirect_cost
    unit_cost = None
    if total_cost is not None and annual_transactions and annual_transactions > 0:
        unit_cost = total_cost / annual_transactions

    current_annual_revenue = None if annual_transactions is None else current_fee * annual_transactions
    proposed_annual_revenue = None if annual_transactions is None else proposed_fee * annual_transactions
    revenue_difference = None
    if current_annual_revenue is not None and proposed_annual_revenue is not None:
        revenue_difference = proposed_annual_revenue - current_annual_revenue

    cost_recovery_ratio = None if not unit_cost else proposed_fee / unit_cost
    customer_fee_change = proposed_fee - current_fee
    customer_fee_change_percentage = None if current_fee == 0 else customer_fee_change / current_fee
    total_customer_cost = proposed_fee + third_party_fee + other_charges

    return {
        "direct_cost": direct_cost,
        "indirect_cost": indirect_cost,
        "annual_transactions": annual_transactions,
        "current_fee": current_fee,
        "proposed_fee": proposed_fee,
        "third_party_fee": third_party_fee,
        "other_mandatory_charges": other_charges,
        "total_cost": total_cost,
        "unit_cost": unit_cost,
        "current_annual_revenue": current_annual_revenue,
        "proposed_annual_revenue": proposed_annual_revenue,
        "revenue_difference": revenue_difference,
        "cost_recovery_ratio": cost_recovery_ratio,
        "customer_fee_change": customer_fee_change,
        "customer_fee_change_percentage": customer_fee_change_percentage,
        "total_customer_cost": total_customer_cost,
    }, missing
