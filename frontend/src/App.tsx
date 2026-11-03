
import { useEffect, useState, type FormEvent, type ChangeEvent } from "react"

type Appointment = {
  id: number
  customer_name: string
  provider_name: string
  appointment_date: string
  appointment_time: string
  status: string
}

type AppointmentForm = {
  customer_name: string
  provider_name: string
  appointment_date: string
  appointment_time: string
  status: string
}

type Page = "overview" | "appointments" | "help"

const API_URL = "/api/appointments/"

const emptyForm: AppointmentForm = {
  customer_name: "",
  provider_name: "",
  appointment_date: "",
  appointment_time: "",
  status: "Pending",
}

export default function App() {
  const [appointments, setAppointments] = useState<Appointment[]>([])
  const [form, setForm] = useState<AppointmentForm>(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selected, setSelected] = useState<Appointment | null>(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [search, setSearch] = useState("")
  const [filter, setFilter] = useState("All")
  const [page, setPage] = useState<Page>("overview")

  async function loadAppointments() {
    setLoading(true)
    setError("")
    try {
      const response = await fetch(API_URL)
      if (!response.ok) throw new Error("Could not load appointments")
      const data: Appointment[] = await response.json()
      setAppointments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadAppointments()
  }, [])

  function handleChange(e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setMessage("")

    const payload = {
      ...form,
      appointment_time: form.appointment_time.length === 5
        ? `${form.appointment_time}:00`
        : form.appointment_time,
    }

    const url = editingId ? `${API_URL}${editingId}` : API_URL
    const method = editingId ? "PUT" : "POST"

    try {
      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const detail = await response.json()
        throw new Error(detail.detail || "Request failed")
      }

      setMessage(editingId ? "Appointment updated successfully!" : "Appointment created successfully!")
      setForm(emptyForm)
      setEditingId(null)
      setShowForm(false)
      setSelected(null)
      setPage("appointments")
      await loadAppointments()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  async function viewAppointment(id: number) {
    setError("")
    try {
      const response = await fetch(`${API_URL}${id}`)
      if (!response.ok) throw new Error("Appointment not found")
      setSelected(await response.json())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  function editAppointment(appointment: Appointment) {
    setEditingId(appointment.id)
    setSelected(null)
    setForm({
      customer_name: appointment.customer_name,
      provider_name: appointment.provider_name,
      appointment_date: appointment.appointment_date,
      appointment_time: appointment.appointment_time.slice(0, 5),
      status: appointment.status,
    })
    setShowForm(true)
    setPage("appointments")
    setMessage("")
    setError("")
  }

  async function deleteAppointment(id: number) {
    if (!window.confirm("Are you sure you want to delete this appointment?")) return

    setError("")
    setMessage("")
    try {
      const response = await fetch(`${API_URL}${id}`, { method: "DELETE" })
      if (!response.ok) throw new Error("Could not delete appointment")
      setMessage("Appointment deleted successfully!")
      setSelected(null)
      await loadAppointments()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  function cancelForm() {
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
    setError("")
  }

  function openNewForm() {
    setEditingId(null)
    setForm(emptyForm)
    setShowForm(true)
    setPage("appointments")
    setMessage("")
    setError("")
  }

  const today = new Date().toISOString().slice(0, 10)
  const pending = appointments.filter(a => a.status === "Pending").length
  const confirmed = appointments.filter(a => a.status === "Confirmed").length
  const completed = appointments.filter(a => a.status === "Completed").length

  const filteredAppointments = appointments.filter(a => {
    const matchesSearch =
      a.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      a.provider_name.toLowerCase().includes(search.toLowerCase())
    const matchesFilter = filter === "All" || a.status === filter
    return matchesSearch && matchesFilter
  })

  const recentAppointments = [...appointments]
    .sort((a, b) => b.id - a.id)
    .slice(0, 5)

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">A</div>
          <span>Appoint<span>HUB</span></span>
        </div>

        <p className="menu-label">WORKSPACE</p>
        <nav className="side-nav">
          <button className={`nav-item ${page === "overview" ? "active" : ""}`} onClick={() => setPage("overview")}>
            <span className="nav-icon">⌂</span> Overview
          </button>
          <button className={`nav-item ${page === "appointments" ? "active" : ""}`} onClick={() => setPage("appointments")}>
            <span className="nav-icon">▤</span> Appointments
          </button>
        </nav>

        <div className="sidebar-bottom">
          <button className="help-card" onClick={() => setPage("help")}>
            <span className="help-icon">✦</span>
            <strong>Need help?</strong>
            <small>Find your way around AppointHUB.</small>
            <span className="help-link">Get assistance →</span>
          </button>

          <div className="profile">
            <div className="avatar">A</div>
            <div>
              <strong>Administrator</strong>
              <small>AppointHUB Admin</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="topbar">
          <div>
            <span className="eyebrow">APPOINTHUB WORKSPACE</span>
            <h2>{page === "overview" ? "Your workspace" : page === "appointments" ? "Appointments" : "Help center"}</h2>
          </div>
          <div className="topbar-right">
            <span className="today-label">◷ &nbsp;{today}</span>
            <div className="top-avatar">A</div>
          </div>
        </header>

        {message && <div className="success-message">{message}</div>}
        {error && <div className="error">{error}</div>}

        {page === "overview" && (
          <>
            <section className="welcome-section">
              <div>
                <span className="eyebrow">YOUR DAILY SNAPSHOT</span>
                <h1>Everything in one place.</h1>
                <p>Keep track of your schedule and stay on top of every appointment.</p>
              </div>
              <button className="primary-btn" onClick={openNewForm}>＋ New appointment</button>
            </section>

            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-top"><span>Total appointments</span><span className="stat-icon purple">▤</span></div>
                <h2>{appointments.length}</h2>
                <small>All recorded appointments</small>
              </div>
              <div className="stat-card">
                <div className="stat-top"><span>Pending</span><span className="stat-icon orange">◷</span></div>
                <h2>{pending}</h2>
                <small>Waiting for confirmation</small>
              </div>
              <div className="stat-card">
                <div className="stat-top"><span>Confirmed</span><span className="stat-icon green">✓</span></div>
                <h2>{confirmed}</h2>
                <small>Ready for appointment</small>
              </div>
              <div className="stat-card">
                <div className="stat-top"><span>Completed</span><span className="stat-icon blue">▣</span></div>
                <h2>{completed}</h2>
                <small>Successfully completed</small>
              </div>
            </section>

            <section className="appointments-section">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">YOUR SCHEDULE</span>
                  <h2>Recent appointments</h2>
                  <p>Your five most recently added appointments.</p>
                </div>
                <button className="secondary-btn" onClick={() => setPage("appointments")}>View all →</button>
              </div>

              {loading ? <p className="empty-state">Loading appointments...</p> :
                recentAppointments.length === 0 ? (
                  <div className="empty-state">
                    <div>▤</div>
                    <h3>Your schedule is clear</h3>
                    <p>Create your first appointment to get started.</p>
                    <button className="primary-btn" onClick={openNewForm}>＋ Create appointment</button>
                  </div>
                ) : (
                  <AppointmentTable
                    items={recentAppointments}
                    onView={viewAppointment}
                    onEdit={editAppointment}
                    onDelete={deleteAppointment}
                  />
                )}
            </section>
          </>
        )}

        {page === "appointments" && (
          <>
            <section className="welcome-section">
              <div>
                <span className="eyebrow">SCHEDULE MANAGEMENT</span>
                <h1>Manage your appointments.</h1>
                <p>Create, update, view, and organize your appointments.</p>
              </div>
              <button className="primary-btn" onClick={openNewForm}>＋ New appointment</button>
            </section>

            {showForm && (
              <section className="form-card">
                <div className="section-heading">
                  <div>
                    <span className="eyebrow">APPOINTMENT DETAILS</span>
                    <h2>{editingId ? "Edit appointment" : "Create new appointment"}</h2>
                    <p>Enter the information below.</p>
                  </div>
                  <button className="close-btn" onClick={cancelForm}>✕</button>
                </div>
                <form onSubmit={handleSubmit} className="appointment-form">
                  <label>Customer name
                    <input name="customer_name" value={form.customer_name} onChange={handleChange} placeholder="Enter customer name" required />
                  </label>
                  <label>Provider name
                    <input name="provider_name" value={form.provider_name} onChange={handleChange} placeholder="Enter provider name" required />
                  </label>
                  <label>Appointment date
                    <input type="date" name="appointment_date" value={form.appointment_date} onChange={handleChange} required />
                  </label>
                  <label>Appointment time
                    <input type="time" name="appointment_time" value={form.appointment_time} onChange={handleChange} required />
                  </label>
                  <label>Status
                    <select name="status" value={form.status} onChange={handleChange}>
                      <option>Pending</option>
                      <option>Confirmed</option>
                      <option>Completed</option>
                      <option>Cancelled</option>
                    </select>
                  </label>
                  <div className="form-actions">
                    <button type="button" className="secondary-btn" onClick={cancelForm}>Cancel</button>
                    <button type="submit" className="primary-btn">{editingId ? "Save changes" : "Create appointment"}</button>
                  </div>
                </form>
              </section>
            )}

            <section className="appointments-section">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">ALL RECORDS</span>
                  <h2>All appointments</h2>
                  <p>Search and manage your appointment records.</p>
                </div>
                <button className="secondary-btn" onClick={() => void loadAppointments()}>↻ Refresh</button>
              </div>

              <div className="table-toolbar">
                <input className="search-input" placeholder="Search customer or provider..." value={search} onChange={e => setSearch(e.target.value)} />
                <select value={filter} onChange={e => setFilter(e.target.value)}>
                  <option>All</option>
                  <option>Pending</option>
                  <option>Confirmed</option>
                  <option>Completed</option>
                  <option>Cancelled</option>
                </select>
              </div>

              {loading ? <p className="empty-state">Loading appointments...</p> :
                filteredAppointments.length === 0 ? (
                  <div className="empty-state">
                    <div>▤</div>
                    <h3>No appointments found</h3>
                    <p>Create an appointment or change your search.</p>
                  </div>
                ) : (
                  <AppointmentTable
                    items={filteredAppointments}
                    onView={viewAppointment}
                    onEdit={editAppointment}
                    onDelete={deleteAppointment}
                  />
                )}
            </section>
          </>
        )}

        {page === "help" && (
          <section className="help-page">
            <span className="eyebrow">SUPPORT & GUIDANCE</span>
            <h1>How can we help?</h1>
            <p className="help-intro">A quick guide to using your AppointHUB workspace.</p>
            <div className="help-grid">
              <article className="help-item">
                <span>＋</span><h3>Create an appointment</h3>
                <p>Open Appointments and select “New appointment”. Fill in the customer, provider, date, time, and status, then save.</p>
                <button className="text-btn" onClick={openNewForm}>Create appointment →</button>
              </article>
              <article className="help-item">
                <span>▤</span><h3>View your appointments</h3>
                <p>Use the Appointments page to see all records. Search by customer or provider and filter by status.</p>
                <button className="text-btn" onClick={() => setPage("appointments")}>Open appointments →</button>
              </article>
              <article className="help-item">
                <span>✎</span><h3>Update or delete</h3>
                <p>Use the Edit action to update a record or Delete to remove an appointment after confirmation.</p>
                <button className="text-btn" onClick={() => setPage("appointments")}>Manage records →</button>
              </article>
              <article className="help-item">
                <span>◉</span><h3>Understand appointment status</h3>
                <p>Pending means awaiting confirmation. Confirmed means scheduled. Completed means finished. Cancelled means no longer scheduled.</p>
              </article>
            </div>
          </section>
        )}
      </main>

      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <div className="details-modal" onClick={e => e.stopPropagation()}>
            <div className="section-heading">
              <div><span className="eyebrow">RECORD #{selected.id}</span><h2>Appointment details</h2></div>
              <button className="close-btn" onClick={() => setSelected(null)}>✕</button>
            </div>
            <p><strong>Customer:</strong> {selected.customer_name}</p>
            <p><strong>Provider:</strong> {selected.provider_name}</p>
            <p><strong>Date:</strong> {selected.appointment_date}</p>
            <p><strong>Time:</strong> {selected.appointment_time}</p>
            <p><strong>Status:</strong> {selected.status}</p>
          </div>
        </div>
      )}
    </div>
  )
}

type AppointmentTableProps = {
  items: Appointment[]
  onView: (id: number) => void
  onEdit: (appointment: Appointment) => void
  onDelete: (id: number) => void
}

function AppointmentTable({ items, onView, onEdit, onDelete }: AppointmentTableProps) {
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Customer</th>
            <th>Provider</th>
            <th>Date & time</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map(appointment => (
            <tr key={appointment.id}>
              <td><strong>{appointment.customer_name}</strong><small>Appointment #{appointment.id}</small></td>
              <td>{appointment.provider_name}</td>
              <td>{appointment.appointment_date}<small>{appointment.appointment_time}</small></td>
              <td><span className={`status-badge ${appointment.status.toLowerCase()}`}>{appointment.status}</span></td>
              <td>
                <div className="action-buttons">
                  <button className="view-action" onClick={() => onView(appointment.id)}>View</button>
                  <button className="edit-action" onClick={() => onEdit(appointment)}>Edit</button>
                  <button className="delete-action" onClick={() => onDelete(appointment.id)}>Delete</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
