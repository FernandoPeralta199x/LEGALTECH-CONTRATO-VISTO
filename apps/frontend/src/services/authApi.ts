import { apiClient } from "@/src/services/apiClient";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  name: string;
  password: string;
  role: string;
}

export interface VerifyEmailPayload {
  email: string;
  token: string;
}

export interface AuthTokenResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
    organization_id: string;
  };
}

export interface RegisterResult {
  user_id: string;
  email: string;
  status: string;
  verification_token: string;
  message: string;
}

export async function login(payload: LoginPayload): Promise<AuthTokenResult> {
  const response = await apiClient.post<AuthTokenResult>("/api/v1/auth/login", payload);
  return response.data;
}

export async function register(payload: RegisterPayload): Promise<RegisterResult> {
  const response = await apiClient.post<RegisterResult>("/api/v1/auth/register", payload);
  return response.data;
}

export async function verifyEmail(payload: VerifyEmailPayload): Promise<AuthTokenResult> {
  const response = await apiClient.post<AuthTokenResult>("/api/v1/auth/verify-email", payload);
  return response.data;
}
