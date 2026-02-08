export type PresetKey = "saas_support" | "auth_incident" | "billing";

export const PRESETS: Record<PresetKey, { name: string; description: string }> = {
  saas_support: {
    name: "SaaS Support Triage (default)",
    description: "Extract product/integration/env + classify severity/intent + build JSON ticket fields"
  },
  auth_incident: {
    name: "Auth / SSO Incident",
    description: "Focus on SSO, IdP, auth errors, and incident routing"
  },
  billing: {
    name: "Billing / Subscription",
    description: "Extract plan, invoice IDs, pricing, and billing intent"
  }
};

export function buildPayload(preset: PresetKey, text: string, threshold: number) {
  const severitySchema = { severity: ["sev0", "sev1", "sev2", "sev3"] };

  const intentSchema =
    preset === "billing"
      ? { intent: ["billing_question", "refund_request", "invoice_issue", "pricing", "cancelation", "other"] }
      : preset === "auth_incident"
      ? { intent: ["sso_issue", "login_issue", "access_request", "incident_report", "how_to", "other"] }
      : { intent: ["bug", "how_to", "access", "incident", "billing", "other"] };

  const entityLabels =
    preset === "billing"
      ? ["customer_name", "company", "plan", "invoice_id", "amount", "currency", "product", "date", "region"]
      : preset === "auth_incident"
      ? ["customer_name", "company", "idp", "integration", "product", "error_code", "environment", "region"]
      : ["customer_name", "company", "product", "feature", "integration", "error_code", "environment", "cloud", "region"];

  // Extract JSON schema format matches the model card usage.
  const jsonSchema =
    preset === "billing"
      ? {
          ticket_fields: [
            "customer_name::str::Customer name",
            "company::str::Company name",
            "plan::str::Plan name if mentioned",
            "invoice_id::str::Invoice ID if present",
            "amount::str::Amount if present",
            "currency::str::Currency if present",
            "intent::str::Billing intent category",
            "severity::str::sev0-sev3",
            "next_queue::str::Routing queue"
          ]
        }
      : preset === "auth_incident"
      ? {
          ticket_fields: [
            "customer_name::str::Customer name",
            "company::str::Company name",
            "idp::str::Identity provider (Okta/AzureAD/etc.)",
            "integration::str::Integration name",
            "error_code::str::Error code if present",
            "environment::str::prod/stage/dev",
            "region::str::Region",
            "intent::str::Intent label",
            "severity::str::sev0-sev3",
            "next_queue::str::Routing queue"
          ]
        }
      : {
          ticket_fields: [
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
            "next_queue::str::Routing queue"
          ]
        };

  return {
    text,
    threshold,
    entityLabels,
    severitySchema,
    intentSchema,
    jsonSchema,
    preset
  };
}
