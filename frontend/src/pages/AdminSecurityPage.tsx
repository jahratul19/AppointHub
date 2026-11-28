import { useEffect, useState } from "react"
import {
  downloadAdminCsv,
  getAdminAuditLogs,
  getFailedLoginSummary,
} from "../services/api"

type Props = { token: string; mode: "security" | "activity" }
type Activity = {
  id: number
  admin_username: string
  target_username: string
  action: string
  reason: string
  ip_address: string | null
  user_agent: string | null
  created_at: string | null
}
type FailureSummary = {
  failed_login_count_7d: number
  by_ip: { ip_address: string; attempts: number }[]
  by_account: { account: string; attempts: number }[]
}

async function saveCsv(response: Response) {
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || "CSV export failed")
  }
  const url = URL.createObjectURL(await response.blob())
  const link = document.createElement("a")
  link.href = url
  link.download = "activity.csv"
  link.click()
  URL.revokeObjectURL(url)
}

export default function AdminSecurityPage({ token, mode }: Props) {
  const [summary, setSummary] = useState<FailureSummary | null>(null)
  const [events, setEvents] = useState<Activity[]>([])
  const [eventType, setEventType] = useState("")
  const [search, setSearch] = useState("")
  const [ipAddress, setIpAddress] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (mode !== "security") return
    let active = true
    setError("")
    getFailedLoginSummary(token)
      .then(async (response) => {
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || "Could not load security summary")
        if (active) setSummary(data)
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load summary"))
    return () => { active = false }
  }, [mode, token])

  useEffect(() => {
    if (mode !== "activity") return
    let active = true
    setError("")
    setLoading(true)
    getAdminAuditLogs(token, { event_type: eventType, search, ip_address: ipAddress })
      .then(async (response) => {
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || "Could not load activity")
        if (active) setEvents(data.events)
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load activity"))
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [mode, token, eventType, search, ipAddress])

  async function exportActivity() {
    try {
      await saveCsv(await downloadAdminCsv(token, "activity", {
        event_type: eventType,
        search,
        ip_address: ipAddress,
      }))
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV export failed")
    }
  }

  if (mode === "security") {
    return (
      <section className="admin-users-page">
        <h2>Security overview</h2>
        <p>Failed sign-in attempts over the last seven days.</p>
        {error && <p className="error">{error}</p>}
        {!summary ? <p>Loading security data...</p> : (
          <>
            <h3>Total failed logins: {summary.failed_login_count_7d}</h3>
            <div className="admin-stats-grid">
              <article className="admin-stat-card">
                <h3>By IP address</h3>
                {summary.by_ip.length ? summary.by_ip.map((item) => (
                  <p key={item.ip_address}>{item.ip_address}: {item.attempts}</p>
                )) : <p>No failed logins.</p>}
              </article>
              <article className="admin-stat-card">
                <h3>By account</h3>
                {summary.by_account.length ? summary.by_account.map((item) => (
                  <p key={item.account}>{item.account}: {item.attempts}</p>
                )) : <p>No failed logins.</p>}
              </article>
            </div>
          </>
        )}
      </section>
    )
  }

  return (
    <section className="admin-users-page">
      <h2>Activity log</h2>
      <p>Authentication, moderation, deletion and export events.</p>
      <div className="users-controls">
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search events" />
        <input value={ipAddress} onChange={(event) => setIpAddress(event.target.value)} placeholder="Filter by IP" />
        <select value={eventType} onChange={(event) => setEventType(event.target.value)}>
          <option value="">All event types</option>
          {["login", "failed_login", "logout", "password_change", "role_change", "ban", "unban", "delete_record", "delete_group", "export_users", "export_records", "export_activity"].map((item) => (
            <option key={item} value={item}>{item.replaceAll("_", " ")}</option>
          ))}
        </select>
        <button type="button" onClick={() => void exportActivity()}>Export CSV</button>
      </div>
      {error && <p className="error">{error}</p>}
      {loading ? <p>Loading activity...</p> : events.length === 0 ? <p>No activity matches these filters.</p> : (
        <div className="admin-users-table">
          <table>
            <thead><tr><th>Actor</th><th>Target / Account</th><th>Event</th><th>Details</th><th>IP</th><th>Browser</th><th>Time</th></tr></thead>
            <tbody>{events.map((event) => (
              <tr key={event.id}>
                <td>{event.admin_username}</td><td>{event.target_username}</td>
                <td>{event.action}</td><td>{event.reason}</td>
                <td>{event.ip_address || "—"}</td><td>{event.user_agent || "—"}</td>
                <td>{event.created_at ? new Date(event.created_at).toLocaleString() : "—"}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </section>
  )
}
