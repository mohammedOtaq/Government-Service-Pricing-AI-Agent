from __future__ import annotations

from typing import Any


CORE_SERVICE_FIELDS = [
    "service_id",
    "service_name",
    "service_type",
    "service_owner",
    "customer_segment",
    "service_description",
]


def get_service_info(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "service_id": data.get("service_id", ""),
        "service_name": data.get("service_name", ""),
        "service_owner": data.get("service_owner", ""),
        "customer_segment": data.get("customer_segment", ""),
        "service_type": data.get("service_type", ""),
    }
