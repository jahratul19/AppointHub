import { useEffect, useState } from "react"
import {
  bulkDeleteAdminGroups,
  bulkDeleteAdminAppointments,
  deleteAdminContentAppointment,
  deleteAdminContentGroup,
  downloadAdminCsv,
  getAdminContentAppointments,
  getAdminContentGroups,
} from "../services/api"

type Props = { token: string }

type RecordRow = {
  id: number
  user_id: number | null
  customer_name: string
  provider_name: string
  doctor_id: number | null
  appointment_date: string
  appointment_time: string
  status: string
  reason: string | null
}

type GroupRow = { id: number; name: string; owner_id: number }

async function saveCsv(response: Response, filename: string) {
  if (!response.ok) {
    const data = await response.json()
    throw new Error(data.detail || "CSV export failed")
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export default function AdminContentPage({ token }: Props) {
  const [tab, setTab] = useState<"records" | "groups">("records")
  const [records, setRecords] = useState<RecordRow[]>([])
  const [recordsPage, setRecordsPage] = useState(1)
  const [recordsTotal, setRecordsTotal] = useState(0)
  const [recordsTotalPages, setRecordsTotalPages] = useState(1)
  const [groups, setGroups] = useState<GroupRow[]>([])
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("all")
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [selectedGroupIds, setSelectedGroupIds] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function loadContent() {
    setLoading(true)
    setError("")
    try {
      if (tab === "records") {
        const response = await getAdminContentAppointments(token, search, status, recordsPage)
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || "Could not load records")
        setRecords(data.records)
        setRecordsTotal(data.total)
        setRecordsTotalPages(data.total_pages)
      } else {
        const response = await getAdminContentGroups(token, search)
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || "Could not load groups")
        setGroups(data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load content")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadContent()
  }, [tab, search, status, recordsPage, token])

  async function deleteRecord(id: number) {
    if (!window.confirm("Permanently delete this record?")) return
    try {
      const response = await deleteAdminContentAppointment(token, id)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || "Could not delete record")
      setMessage("Record deleted.")
      await loadContent()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete record")
    }
  }

  async function deleteSelected() {
    if (!selectedIds.length || !window.confirm(`Delete ${selectedIds.length} records?`)) return
    try {
      const response = await bulkDeleteAdminAppointments(token, selectedIds)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || "Could not delete records")
      setSelectedIds([])
      setMessage(`${data.deleted_count} records deleted.`)
      await loadContent()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete records")
    }
  }

  async function deleteGroup(group: GroupRow) {
    if (!window.confirm(`Permanently delete group "${group.name}"?`)) return
    try {
      const response = await deleteAdminContentGroup(token, group.id)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || "Could not delete group")
      setMessage("Group and its shared content deleted.")
      await loadContent()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete group")
    }
  }

  async function deleteSelectedGroups() {
    if (!selectedGroupIds.length || !window.confirm(`Delete ${selectedGroupIds.length} groups and their resources?`)) return
    try {
      const response = await bulkDeleteAdminGroups(token, selectedGroupIds)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || "Could not delete groups")
      setSelectedGroupIds([])
      setMessage(`${data.deleted_count} groups deleted.`)
      await loadContent()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete groups")
    }
  }

  async function exportRecords() {
    try {
      await saveCsv(
        await downloadAdminCsv(token, "records", { search, status }),
        "records.csv",
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV export failed")
    }
  }

  return (
    <section className="admin-users-page">
      <h2>Content moderation</h2>
      <p>Search and moderate all appointments and shared groups.</p>
      <div className="users-controls">
        <button type="button" onClick={() => setTab("records")}>Records</button>
        <button type="button" onClick={() => setTab("groups")}>Groups</button>
        <input
          value={search}
          onChange={(event) => {
            setSearch(event.target.value)
            setRecordsPage(1)
          }}
          placeholder={tab === "records" ? "Search patient, doctor or reason" : "Search group"}
          aria-label="Search content"
        />
        {tab === "records" && (
          <select value={status} onChange={(event) => {
            setStatus(event.target.value)
            setRecordsPage(1)
          }}>
            <option value="all">All statuses</option>
            <option value="Pending">Pending</option>
            <option value="Confirmed">Confirmed</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        )}
        {tab === "records" && (
          <button type="button" onClick={() => void exportRecords()}>Export CSV</button>
        )}
      </div>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="error">{error}</p>}
      {loading ? <p>Loading content...</p> : tab === "records" ? (
        records.length === 0 ? <p>No records found.</p> : (
          <>
            <button type="button" disabled={!selectedIds.length} onClick={() => void deleteSelected()}>
              Delete selected ({selectedIds.length})
            </button>
            <div className="admin-users-table">
              <table>
                <thead><tr><th>Select</th><th>ID</th><th>Owner ID</th><th>Patient</th><th>Doctor</th><th>Date</th><th>Reason</th><th>Status</th><th>Action</th></tr></thead>
                <tbody>{records.map((item) => (
                  <tr key={item.id}>
                    <td><input
                      type="checkbox"
                      checked={selectedIds.includes(item.id)}
                      onChange={(event) => setSelectedIds((previous) => event.target.checked
                        ? [...previous, item.id]
                        : previous.filter((id) => id !== item.id))}
                      aria-label={`Select record ${item.id}`}
                    /></td>
                    <td>{item.id}</td><td>{item.user_id ?? "—"}</td>
                    <td>{item.customer_name}</td><td>{item.provider_name}</td>
                    <td>{item.appointment_date} {item.appointment_time}</td>
                    <td>{item.reason || "—"}</td><td>{item.status}</td>
                    <td><button type="button" onClick={() => void deleteRecord(item.id)}>Delete</button></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            <div className="users-pagination">
              <p>Page {recordsPage} of {recordsTotalPages} ({recordsTotal} records)</p>
              <div>
                <button
                  type="button"
                  onClick={() => setRecordsPage((current) => current - 1)}
                  disabled={recordsPage <= 1 || loading}
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setRecordsPage((current) => current + 1)}
                  disabled={recordsPage >= recordsTotalPages || loading}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )
      ) : groups.length === 0 ? <p>No groups found.</p> : (
        <>
          <button type="button" disabled={!selectedGroupIds.length} onClick={() => void deleteSelectedGroups()}>
            Delete selected groups ({selectedGroupIds.length})
          </button>
          <div className="admin-users-table">
            <table>
              <thead><tr><th>Select</th><th>ID</th><th>Name</th><th>Owner ID</th><th>Action</th></tr></thead>
              <tbody>{groups.map((group) => (
                <tr key={group.id}>
                  <td><input
                    type="checkbox"
                    checked={selectedGroupIds.includes(group.id)}
                    onChange={(event) => setSelectedGroupIds((previous) => event.target.checked
                      ? [...previous, group.id]
                      : previous.filter((id) => id !== group.id))}
                    aria-label={`Select group ${group.id}`}
                  /></td>
                  <td>{group.id}</td><td>{group.name}</td><td>{group.owner_id}</td>
                  <td><button type="button" onClick={() => void deleteGroup(group)}>Delete</button></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </>
      )}
    </section>
  )
}
