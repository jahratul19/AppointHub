
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

export function updateProfile(
  token: string,
  payload: { username: string; email: string }
) {
  return fetch(`${AUTH_URL}/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })
}

export function changePassword(
  token: string,
  payload: { current_password: string; new_password: string }
) {
  return fetch(`${AUTH_URL}/change-password`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })
}

export function getAdminDashboardStats(token: string) {
  return fetch(`${API_BASE_URL}/api/admin/dashboard/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export function getAdminUsers(token: string, page: number = 1, limit: number = 10) {
  return fetch(
    `${API_BASE_URL}/api/admin/users?page=${page}&limit=${limit}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )
}


export function banAdminUser(
  token: string,
  userId: number,
  reason: string
) {
  return fetch(`${API_BASE_URL}/api/admin/users/${userId}/ban`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reason }),
  })
}

export function unbanAdminUser(
  token: string,
  userId: number,
  reason: string
) {
  return fetch(`${API_BASE_URL}/api/admin/users/${userId}/unban`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reason }),
  })
}

export function updateAdminUserRole(
  token: string,
  userId: number,
  role: string
) {
  return fetch(`${API_BASE_URL}/api/admin/users/${userId}/role`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ role }),
  })
}

export function revokeAdminUserSessions(
  token: string,
  userId: number
) {
  return fetch(
    `${API_BASE_URL}/api/admin/users/${userId}/sessions`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  )
}

export function getAdminAuditLogs(token: string) {
  return fetch(`${API_BASE_URL}/api/admin/audit-logs`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
}

export function bulkAdminUserAction(
  token: string,
  userIds: number[],
  action: "ban" | "unban",
  reason: string
) {
  return fetch(`${API_BASE_URL}/api/admin/users/bulk-action`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      user_ids: userIds,
      action,
      reason,
    }),
  })
}