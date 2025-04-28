import { deleteCookie, getCookie } from 'cookies-next';

interface TokenPayload {
  access_token?: string;
  refresh_token?: string;
}

export function removeToken(): void {
  deleteCookie("user");
}

export function getToken(): string | undefined {
  const authCookie = getCookie("user");
  if (typeof authCookie === "string") {
    const tokens = JSON.parse(authCookie) as TokenPayload;
    return tokens.access_token;
  }
  return undefined;
}

export function getRefreshToken(): string | undefined {
  const authCookie = getCookie("user");
  if (typeof authCookie === "string") {
    const tokens = JSON.parse(authCookie) as TokenPayload;
    return tokens.refresh_token;
  }
  return undefined;
}
