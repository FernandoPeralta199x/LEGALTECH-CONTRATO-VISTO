import assert from "node:assert/strict";
import test from "node:test";

import { listOperationalReports } from "./reports";

class MemoryStorage {
  private values = new Map<string, string>();

  getItem(key: string) {
    return this.values.get(key) ?? null;
  }

  removeItem(key: string) {
    this.values.delete(key);
  }

  setItem(key: string, value: string) {
    this.values.set(key, value);
  }
}

Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: new MemoryStorage()
});

function aggregatePayload(report: Record<string, unknown> | null) {
  return {
    case: {
      id: "11111111-1111-4111-8111-111111111111",
      request_id: "22222222-2222-4222-8222-222222222222",
      code: "CASO-LOCAL-0001",
      organization_id: "33333333-3333-4333-8333-333333333333",
      created_by: "44444444-4444-4444-8444-444444444444",
      product_type: "analise_contratual",
      product_label: "Análise contratual",
      title: "Caso com relatório",
      description: "Caso operacional",
      status: "report_ready",
      progress: 90,
      risk_level: "medium",
      recommendation: "proceed_with_caution",
      source_mode: "mock",
      is_local_simulation: true,
      created_at: "2026-06-01T10:00:00.000Z",
      updated_at: "2026-06-01T11:00:00.000Z"
    },
    request: null,
    parties: [],
    documents: [],
    timeline: [],
    triage_modules: [],
    provider_results: [],
    report,
    summary: {
      case_id: "11111111-1111-4111-8111-111111111111",
      organization_id: "33333333-3333-4333-8333-333333333333",
      parties_count: 0,
      documents_count: 0,
      timeline_count: 0,
      triage_status: "not_started",
      report_status: report ? "ready" : "not_started",
      risk_level: "medium",
      recommendation: "proceed_with_caution",
      progress: 90,
      latest_event_at: null,
      source_mode: "mock",
      updated_at: "2026-06-01T11:00:00.000Z"
    }
  };
}

test("listOperationalReports returns only reports present in case aggregates", async () => {
  let requestCount = 0;
  globalThis.fetch = (async () => {
    requestCount += 1;

    if (requestCount === 1) {
      return Response.json({
        success: true,
        data: {
          items: [
            {
              id: "11111111-1111-4111-8111-111111111111",
              case_id: "11111111-1111-4111-8111-111111111111",
              code: "CASO-LOCAL-0001",
              title: "Caso com relatório",
              product_type: "analise_contratual",
              product_label: "Análise contratual",
              status: "report_ready",
              progress: 90,
              risk_level: "medium",
              parties_count: 0,
              documents_count: 0,
              triage_status: "completed",
              report_status: "ready",
              source_mode: "mock",
              created_at: "2026-06-01T10:00:00.000Z",
              updated_at: "2026-06-01T11:00:00.000Z"
            }
          ],
          page: 1,
          page_size: 20,
          total: 1,
          total_pages: 1
        }
      });
    }

    return Response.json({
      success: true,
      data: aggregatePayload({
        id: "report-operational-1",
        case_id: "11111111-1111-4111-8111-111111111111",
        organization_id: "33333333-3333-4333-8333-333333333333",
        status: "ready",
        version: 1,
        summary: "Relatório operacional mock.",
        findings: ["Achado"],
        legal_risks: [],
        commercial_risks: [],
        reputational_risks: [],
        contractual_risks: [],
        missing_information: [],
        recommendation: "proceed_with_caution",
        confidence: 0.5,
        limitations: ["Mock local."],
        source_refs: [{ type: "case", id: "11111111-1111-4111-8111-111111111111" }],
        generated_by: "mock_ai_report_provider",
        generated_at: "2026-06-01T11:00:00.000Z",
        updated_at: "2026-06-01T11:00:00.000Z"
      })
    });
  }) as typeof fetch;

  const result = await listOperationalReports();

  assert.equal(result.source, "api");
  assert.equal(result.data.length, 1);
  assert.equal(result.data[0].report.id, "report-operational-1");
  assert.equal(result.data[0].report.caseId, "11111111-1111-4111-8111-111111111111");
});

