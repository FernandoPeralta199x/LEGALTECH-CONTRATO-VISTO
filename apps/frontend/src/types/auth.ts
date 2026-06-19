export const DEV_ROLES = ["owner", "admin", "analyst", "client", "support"] as const;

export type DevRole = (typeof DEV_ROLES)[number];

export type DevSessionSource = "pasted";

export type DevSession = {
  email: string;
  expiresAt?: string;
  issuedAt: string;
  organizationId: string;
  role: DevRole;
  source: DevSessionSource;
  token: string;
  userId: string;
};

export type DevLoginInput = {
  role: DevRole;
  token?: string;
};

export type DecodedDevJwt = {
  aud?: string;
  email?: string;
  exp?: number;
  iat?: number;
  iss?: string;
  sub?: string;
  token_use?: string;
  "custom:organization_id"?: string;
  "custom:role"?: string;
  organization_id?: string;
  role?: string;
};
