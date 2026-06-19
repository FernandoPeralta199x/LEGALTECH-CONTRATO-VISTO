import type { Case, Report } from "../../types";
import { getCaseAggregate, listCases } from "./cases";
import type { ServiceResult } from "./fallback";

export type OperationalReportListItem = {
  caseData: Case;
  report: Report;
  sourceMode: Case["sourceMode"];
};

export async function listOperationalReports(): Promise<
  ServiceResult<OperationalReportListItem[]>
> {
  const casesResult = await listCases();
  const reports: OperationalReportListItem[] = [];

  for (const legalCase of casesResult.data) {
    const aggregateResult = await getCaseAggregate(legalCase.id);
    if (!aggregateResult.data.report) {
      continue;
    }

    reports.push({
      caseData: aggregateResult.data.case,
      report: aggregateResult.data.report,
      sourceMode: aggregateResult.data.summary.sourceMode
    });
  }

  return {
    data: reports,
    fallbackReason: casesResult.fallbackReason,
    source: casesResult.source
  };
}
