
import type { AppointmentForm, AuthMode } from "../types"

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "")
const API_URL = `${API_BASE_URL}/api/appointments/`
const AUTH_URL = `${API_BASE_URL}/api/auth`

export function getAppointments() {
  return fetch(API_URL)
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

export function getAppointment(id: number) {
  return fetch(`${API_URL}${id}`)
}

export function deleteAppointment(id: number): Promise<Response> {
  return fetch(`${API_URL}${id}`, {
    method: "DELETE",
  })
}
