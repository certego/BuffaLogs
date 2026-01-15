import { deleteCookie, getCookie } from 'cookies-next';

interface TokenPayload {
  tokens?: {
    access?: string;
    refresh?: string;
  };
  access_token?: string;
  refresh_token?: string;
}

export function removeToken(): void {
  deleteCookie("user");
}

export function getToken(): string | undefined {
  const authCookie = getCookie("user");
  if (typeof authCookie === "string") {
    const data = JSON.parse(authCookie) as TokenPayload;
    // Handle both formats: {tokens: {access, refresh}} and {access_token, refresh_token}
    return data.tokens?.access || data.access_token;
  }
  return undefined;
}

export function getRefreshToken(): string | undefined {
  const authCookie = getCookie("user");
  if (typeof authCookie === "string") {
    const data = JSON.parse(authCookie) as TokenPayload;
    // Handle both formats: {tokens: {access, refresh}} and {access_token, refresh_token}
    return data.tokens?.refresh || data.refresh_token;
  }
  return undefined;
}
