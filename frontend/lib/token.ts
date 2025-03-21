import { deleteCookie, getCookie } from 'cookies-next';

export function removeToken(): void {
  deleteCookie("user");;
}

export function getToken(): String | undefined {
  const authCookie= getCookie("user");
  if(typeof authCookie === 'string') {
    const tokens = JSON.parse(authCookie);
    return tokens?.access_token;
  }
  return undefined;
}

export function getRefreshToken(): String | undefined  {
  const authCookie= getCookie('user');
  if(typeof authCookie === 'string') {
    const tokens = JSON.parse(authCookie);
    return tokens?.refresh_token;
  }
  return undefined;
} 