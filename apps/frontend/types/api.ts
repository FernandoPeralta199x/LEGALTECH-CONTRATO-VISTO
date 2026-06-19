import type { SourceMode } from "./domain";

export type ApiError = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};

type ApiEnvelopeBase = {
  request_id: string;
  source_mode: SourceMode;
  timestamp: string;
};

export type ApiSuccessResponse<T> = ApiEnvelopeBase & {
  success: true;
  data: T;
  error: null;
  message?: string;
};

export type ApiErrorResponse = ApiEnvelopeBase & {
  success: false;
  data: null;
  error: ApiError;
};

export type ApiResponse<T> = ApiSuccessResponse<T> | ApiErrorResponse;

export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};
