import cookie from "cookie";
import { getToken, removeToken } from "./token";
import { LOGIN_URL, LOGOUT_URL, ME_URL } from "./constants";

export const loginUser = async (email: String, password: String) => {
  const res = await fetch(LOGIN_URL, {
    body: JSON.stringify({ email, password }),
    method: "POST",
    headers: { "Content-type": "application/json;charset=UTF-8" },
  });
  const { status } = res;
  if (status !== 200) {
    console.log("Error While Authenticating");
    return {
      error: "Invalid Credentials!"
    };
  }
  const data = res.json();
  return data;
};

export const logoutUser = async () => {
  const res = await fetch(LOGOUT_URL, {
    method: "POST",
    headers: {
      "Content-type": "application/json;charset=UTF-8",
      Authorization: `Bearer ${getToken()}`,
    },
  });
  const data = await res.json();
  removeToken();
  return data;
};

export const whoAmI = async () => {
  const res = await fetch(ME_URL, {
    headers: {
      Authorization: `Bearer ${getToken()}`,
      "Content-type": "application/json;charset=UTF-8",
    },
    method: "GET",
  });
  const data = await res.json();
  const result = data?.results[0];
  return result;
};

export function parseCookies(req: { headers: { cookie: any; }; }) {
  return cookie.parse(req ? req.headers.cookie || "" : document.cookie);
}