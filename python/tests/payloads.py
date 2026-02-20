"""
Build /analyze request payloads matching the frontend (lib/schemas.ts).
Used by tests to call the triage API.
"""
from __future__ import annotations

from typing import Any, Dict, List

PRESETS = ("saas_support", "auth_incident", "billing")


def build_analyze_payload(preset: str, text: str, threshold: float) -> Dict[str, Any]:
    severity_schema = {"severity": ["sev0", "sev1", "sev2", "sev3"]}
    if preset == "billing":
        intent_schema = {
            "intent": [
                "billing_question",
                "refund_request",
                "invoice_issue",
                "pricing",
                "cancelation",
                "other",
            ]
        }
        entity_labels = [
            "customer_name",
            "company",
            "plan",
            "invoice_id",
            "amount",
            "currency",
            "product",
            "date",
            "region",
        ]
        json_schema = {
            "ticket_fields": [
                "customer_name::str::Customer name",
                "company::str::Company name",
                "plan::str::Plan name if mentioned",
                "invoice_id::str::Invoice ID if present",
                "amount::str::Amount if present",
                "currency::str::Currency if present",
                "intent::str::Billing intent category",
                "severity::str::sev0-sev3",
                "next_queue::str::Routing queue",
            ]
        }
    elif preset == "auth_incident":
        intent_schema = {
            "intent": [
                "sso_issue",
                "login_issue",
                "access_request",
                "incident_report",
                "how_to",
                "other",
            ]
        }
        entity_labels = [
            "customer_name",
            "company",
            "idp",
            "integration",
            "product",
            "error_code",
            "environment",
            "region",
        ]
        json_schema = {
            "ticket_fields": [
                "customer_name::str::Customer name",
                "company::str::Company name",
                "idp::str::Identity provider (Okta/AzureAD/etc.)",
                "integration::str::Integration name",
                "error_code::str::Error code if present",
                "environment::str::prod/stage/dev",
                "region::str::Region",
                "intent::str::Intent label",
                "severity::str::sev0-sev3",
                "next_queue::str::Routing queue",
            ]
        }
    else:
        intent_schema = {
            "intent": ["bug", "how_to", "access", "incident", "billing", "other"]
        }
        entity_labels = [
            "customer_name",
            "company",
            "product",
            "feature",
            "integration",
            "error_code",
            "environment",
            "cloud",
            "region",
        ]
        json_schema = {
            "ticket_fields": [
                "customer_name::str::Customer name",
                "company::str::Company name",
                "product::str::Product area",
                "feature::str::Feature area",
                "integration::str::Integration mentioned",
                "error_code::str::Error code if present",
                "environment::str::prod/stage/dev",
                "cloud::str::aws/gcp/azure if present",
                "region::str::Region",
                "intent::str::Intent label",
                "severity::str::sev0-sev3",
                "next_queue::str::Routing queue",
            ]
        }

    return {
        "text": text,
        "threshold": threshold,
        "entityLabels": entity_labels,
        "severitySchema": severity_schema,
        "intentSchema": intent_schema,
        "jsonSchema": json_schema,
        "preset": preset,
    }
