
import type { AppointmentForm, AuthMode, DoctorForm } from "../types"

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "")
const API_URL = `${API_BASE_URL}/api/appointments/`
const AUTH_URL = `${API_BASE_URL}/api/auth`

export async function authenticatedFetch(
  token: string,
  url: string,
  options: RequestInit = {},
): Promise<Response> {
  const withToken = (accessToken: string): RequestInit => {
    const headers = new Headers(options.headers)
    headers.set("Authorization", `Bearer ${accessToken}`)
    return { ...options, headers }
  }

  const response = await fetch(url, withToken(token))
  if (response.status !== 401) return response

  const refreshResponse = await refreshAccessToken()
  if (!refreshResponse.ok) {
    window.dispatchEvent(new Event("app-session-expired"))
    return response
  }

  const refreshed = await refreshResponse.json()
  window.dispatchEvent(new CustomEvent("app-access-token", {
    detail: refreshed.access_token,
  }))
  const retryResponse = await fetch(url, withToken(refreshed.access_token))
  if (retryResponse.status === 401) {
    window.dispatchEvent(new Event("app-session-expired"))
  }
  return retryResponse
}


export function getAppointments(token: string) {
  return authenticatedFetch(token, API_URL)
}

export function getDoctors() {
  return fetch(`${API_BASE_URL}/api/doctors`)
}

export function getAdminDoctors(token: string) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/doctors`)
}

export function createAdminDoctor(token: string, payload: DoctorForm) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/doctors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export function updateAdminDoctor(
  token: string,
  doctorId: number,
  payload: DoctorForm,
) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/doctors/${doctorId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
}

export function deactivateAdminDoctor(token: string, doctorId: number) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/doctors/${doctorId}/deactivate`,
    { method: "POST" },
  )
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
  payload: Omit<AppointmentForm, "doctor_id"> & { doctor_id: number },
) {
  const url = id ? `${API_URL}${id}` : API_URL
  const method = id ? "PUT" : "POST"

  return authenticatedFetch(token, url, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })
}

export function getAppointment(id: number, token: string) {
  return authenticatedFetch(token, `${API_URL}${id}`)
}

export function deleteAppointment(id: number, token: string): Promise<Response> {
  return authenticatedFetch(token, `${API_URL}${id}`, {
    method: "DELETE",
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

export function getMyProfile(token: string) {
  return authenticatedFetch(token, `${AUTH_URL}/me`)
}

export function getMySessions(token: string) {
  return authenticatedFetch(token, `${AUTH_URL}/sessions`)
}

export function revokeMySession(token: string, sessionId: number) {
  return authenticatedFetch(token, `${AUTH_URL}/sessions/${sessionId}`, {
    method: "DELETE",
  })
}

export function getAdminUserDetail(token: string, userId: number) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/users/${userId}`)
}

export function getFailedLoginSummary(token: string) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/security/failed-logins`)
}

export function getAdminContentAppointments(
  token: string,
  search: string,
  status: string,
  page = 1,
) {
  const query = new URLSearchParams()
  query.set("page", String(page))
  if (search) query.set("search", search)
  if (status && status !== "all") query.set("status", status)
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/content/appointments?${query.toString()}`,
  )
}

export function getAdminContentGroups(token: string, search: string) {
  const query = new URLSearchParams()
  if (search) query.set("search", search)
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/content/groups?${query.toString()}`,
  )
}

export function deleteAdminContentAppointment(token: string, appointmentId: number) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/content/appointments/${appointmentId}`,
    { method: "DELETE" },
  )
}

export function bulkDeleteAdminAppointments(token: string, recordIds: number[]) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/content/appointments/bulk-delete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ record_ids: recordIds }),
    },
  )
}

export function deleteAdminContentGroup(token: string, groupId: number) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/content/groups/${groupId}`,
    { method: "DELETE" },
  )
}

export function bulkDeleteAdminGroups(token: string, groupIds: number[]) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/content/groups/bulk-delete`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ record_ids: groupIds }),
    },
  )
}

export function downloadAdminCsv(
  token: string,
  kind: "users" | "records" | "activity",
  filters: Record<string, string> = {},
) {
  const query = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== "all") query.set(key, value)
  })
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/export/${kind}.csv?${query.toString()}`,
  )
}

export function updateProfile(
  token: string,
  payload: { username: string; email: string }
) {
  return authenticatedFetch(token, `${AUTH_URL}/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })
}

export function changePassword(
  token: string,
  payload: { current_password: string; new_password: string }
) {
  return authenticatedFetch(token, `${AUTH_URL}/change-password`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })
}

export function getAdminDashboardStats(token: string) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/dashboard/stats`)
}

export function getAdminUsers(
  token: string,
  page: number = 1,
  limit: number = 10,
  filters: { search?: string; role?: string; status?: string } = {},
) {
  const query = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  })
  if (filters.search) query.set("search", filters.search)
  if (filters.role && filters.role !== "all") query.set("role", filters.role)
  if (filters.status && filters.status !== "all") query.set("status", filters.status)
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/users?${query.toString()}`,
  )
}


export function banAdminUser(
  token: string,
  userId: number,
  reason: string
) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/users/${userId}/ban`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ reason }),
  })
}

export function unbanAdminUser(
  token: string,
  userId: number,
  reason: string
) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/users/${userId}/unban`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ reason }),
  })
}

export function updateAdminUserRole(
  token: string,
  userId: number,
  role: string
) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/users/${userId}/role`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ role }),
  })
}

export function revokeAdminUserSessions(
  token: string,
  userId: number
) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/users/${userId}/sessions`,
    { method: "DELETE" },
  )
}

export function getAdminAuditLogs(
  token: string,
  filters: { event_type?: string; search?: string; ip_address?: string } = {},
) {
  const query = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value)
  })
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/admin/audit-logs?${query.toString()}`,
  )
}

export function bulkAdminUserAction(
  token: string,
  userIds: number[],
  action: "ban" | "unban",
  reason: string
) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/admin/users/bulk-action`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_ids: userIds,
      action,
      reason,
    }),
  })
}

export function getGroups(token: string) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups`)
}

export function createGroup(token: string, name: string) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  })
}

export function renameGroup(token: string, groupId: number, name: string) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups/${groupId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  })
}

export function deleteGroup(token: string, groupId: number) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups/${groupId}`, {
    method: "DELETE",
  })
}

export function addGroupMember(
  token: string,
  groupId: number,
  email: string
) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups/${groupId}/members`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  })
}

export function removeGroupMember(token: string, groupId: number, userId: number) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/groups/${groupId}/members/${userId}`,
    { method: "DELETE" },
  )
}

export function getGroupMembers(token: string, groupId: number) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups/${groupId}/members`)
}

export function updateGroupPermissions(
  token: string,
  groupId: number,
  userId: number,
  permissions: {
    can_view: boolean
    can_create: boolean
    can_edit: boolean
    can_delete: boolean
    can_manage_members: boolean
  }
) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/groups/${groupId}/members/${userId}/permissions`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(permissions),
    }
  )
}

export function getGroupResources(token: string, groupId: number) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups/${groupId}/resources`)
}

export function createGroupResource(
  token: string,
  groupId: number,
  title: string,
  description: string
) {
  return authenticatedFetch(token, `${API_BASE_URL}/api/groups/${groupId}/resources`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title, description }),
  })
}

export function updateGroupResource(
  token: string,
  groupId: number,
  resourceId: number,
  title: string,
  description: string
) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/groups/${groupId}/resources/${resourceId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title, description }),
    }
  )
}

export function deleteGroupResource(
  token: string,
  groupId: number,
  resourceId: number
) {
  return authenticatedFetch(
    token,
    `${API_BASE_URL}/api/groups/${groupId}/resources/${resourceId}`,
    {
      method: "DELETE",
    }
  )
}