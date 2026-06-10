import type {
  ApiError,
  ScenarioRequest,
  SequenceRiskRequest,
  SequenceRiskResponse,
  SimulateResponse,
  SuccessRateCurveRequest,
  SuccessRateCurveResponse,
} from "./types";

// In production this is set to same-origin "/api" and routed to the backend
// by the ingress; in dev it points straight at uvicorn.
const API_BASE = import.meta.env.PUBLIC_API_BASE_URL ?? "/api";

interface ValidationIssue {
  loc?: unknown[];
  msg?: string;
}

function isValidationIssues(detail: unknown): detail is ValidationIssue[] {
  return Array.isArray(detail) && detail.every((d) => typeof d === "object" && d !== null && "msg" in d);
}

function formatDetail(detail: unknown, status: number): string {
  if (typeof detail === "string") return detail;
  if (isValidationIssues(detail)) {
    return detail
      .map((issue) => {
        const field = (issue.loc ?? []).filter((p) => p !== "body").join(".");
        return field ? `${field}: ${issue.msg}` : (issue.msg ?? "Invalid request");
      })
      .join("; ");
  }
  return detail ? JSON.stringify(detail) : `HTTP ${status}`;
}

export class ApiRequestError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(formatDetail(detail, status));
    this.name = "ApiRequestError";
    this.status = status;
    this.detail = detail;
  }
}

async function post<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiRequestError(0, "Could not reach the simulation API. Please try again.");
  }

  if (!res.ok) {
    let detail: unknown = `HTTP ${res.status}`;
    try {
      const data = (await res.json()) as ApiError;
      detail = data?.error?.message ?? data?.error?.type ?? detail;
    } catch {
      // ignore - non-JSON error body
    }
    throw new ApiRequestError(res.status, detail);
  }

  return (await res.json()) as TRes;
}

export function simulate(req: ScenarioRequest): Promise<SimulateResponse> {
  return post("/simulate", req);
}

export function successRateCurve(req: SuccessRateCurveRequest): Promise<SuccessRateCurveResponse> {
  return post("/success-rate-curve", req);
}

export function sequenceRisk(req: SequenceRiskRequest): Promise<SequenceRiskResponse> {
  return post("/sequence-risk", req);
}
