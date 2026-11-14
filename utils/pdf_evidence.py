from io import BytesIO
import math
import re

import pdfplumber


TEXT = {
    "service_id", "service_name", "service_type", "service_owner",
    "customer_segment", "service_description", "channel", "duplication_risk",
    "benchmark_limitation_justification",
}
FLAGS = {
    "is_mandatory", "is_recurring", "service_is_value_added", "clear_beneficiary",
    "legal_authority_available", "fee_collectable", "renewal_justified",
    "customer_journey_reviewed", "benchmark_available",
}
NUMBERS = {
    "renewal_period_months", "annual_transactions", "current_fee", "proposed_fee",
    "benchmark_fee", "direct_cost", "indirect_cost", "automation_level_percentage",
    "average_processing_time_minutes", "third_party_fee", "other_mandatory_charges",
}
REQUIRED = TEXT & {
    "service_id", "service_name", "service_type", "service_owner",
    "customer_segment", "service_description",
} | FLAGS & {
    "service_is_value_added", "clear_beneficiary", "legal_authority_available",
    "fee_collectable",
} | {"annual_transactions", "direct_cost", "indirect_cost", "current_fee", "proposed_fee"}
LABELS = {
    "process_owner": "service_owner",
    "current_service_fee": "current_fee",
    "proposed_service_fee": "proposed_fee",
    "annual_direct_cost": "direct_cost",
    "annual_indirect_cost": "indirect_cost",
}


def parse_field(key, value):
    if key in TEXT and value:
        return value
    if key in FLAGS and value.lower() in {"yes", "no", "true", "false"}:
        return value.lower() in {"yes", "true"}
    if key in NUMBERS:
        cleaned = re.sub(r"(?i)\bAED\b|%$", "", value).strip()
        if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", cleaned):
            raise ValueError
        number = float(cleaned.replace(",", ""))
        if not math.isfinite(number) or (key == "automation_level_percentage" and number > 100):
            raise ValueError
        if key in {"annual_transactions", "renewal_period_months"}:
            if number <= 0 or not number.is_integer():
                raise ValueError
            return int(number)
        return number
    raise ValueError


def extract_pdf(content):
    pages, fields, sources, issues, disputed = [], {}, {}, [], set()
    with pdfplumber.open(BytesIO(content)) as document:
        for number, page in enumerate(document.pages, 1):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            pages.append((number, text, tables))
            pairs = [line.split(":", 1) for line in text.splitlines() if ":" in line]
            for table in tables:
                if not table:
                    continue
                pairs.extend(row for row in table if len(row) == 2)
                if len(table) >= 2:
                    for row in table[1:]:
                        pairs.extend(zip(table[0], row))
            for label, raw in pairs:
                key = re.sub(r"[^a-z0-9]+", "_", (label or "").lower()).strip("_")
                key = LABELS.get(key, key)
                if key not in TEXT | FLAGS | NUMBERS or key in disputed:
                    continue
                try:
                    value = parse_field(key, (raw or "").strip())
                except ValueError:
                    issues.append(f"Page {number}: invalid value for {key}.")
                    continue
                if key in fields and fields[key] != value:
                    fields.pop(key)
                    sources.pop(key)
                    disputed.add(key)
                    issues.append(f"Page {number}: conflicting values for {key}.")
                    continue
                fields[key] = value
                sources.setdefault(key, number)
    return pages, fields, sources, issues
