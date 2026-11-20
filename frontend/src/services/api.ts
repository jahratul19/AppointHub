
import type { AppointmentForm, AuthMode } from "../types"

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "")
const API_URL = `${API_BASE_URL}/api/appointments/`
const AUTH_URL = `${API_BASE_URL}/api/auth`


export function getAppointments(token: string) {
  return fetch(API_URL, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export function authenticate(
  authMode: AuthMode,
  payload: { username?: string; email: string; password: string }
) {
  const endpoint =
    authMode === "register"
      ? `${AUTH_URL}/register`
      : `${AUTH_URL}/login`

  return fetch(endpoint, {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })
}

export function saveAppointment(
  id: number | null,
  token: string,
  payload: AppointmentForm
) {
  const url = id ? `${API_URL}${id}` : API_URL
  const method = id ? "PUT" : "POST"

  return fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })
}

export function getAppointment(id: number, token: string) {
  return fetch(`${API_URL}${id}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export function deleteAppointment(id: number, token: string): Promise<Response> {
  return fetch(`${API_URL}${id}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export function refreshAccessToken() {
  return fetch(`${AUTH_URL}/refresh`, {
    method: "POST",
    credentials: "include",
  })
}

export function logout() {
  return fetch(`${AUTH_URL}/logout`, {
    method: "POST",
    credentials: "include",
  })
}
