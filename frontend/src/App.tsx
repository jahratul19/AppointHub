
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

      setMessage(editingId
        ? "Appointment updated successfully!"
        : "Appointment created successfully!")

      setForm(emptyForm)
      setEditingId(null)
      setShowForm(false)
      setSelected(null)
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
      const data: Appointment = await response.json()
      setSelected(data)
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

  const today = new Date().toISOString().slice(0, 10)

  const filteredAppointments = appointments.filter((appointment) => {
    const matchesSearch =
      appointment.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      appointment.provider_name.toLowerCase().includes(search.toLowerCase())

    const matchesFilter = filter === "All" || appointment.status === filter
    return matchesSearch && matchesFilter
  })

  const pending = appointments.filter(a => a.status === "Pending").length
  const confirmed = appointments.filter(a => a.status === "Confirmed").length
  const completed = appointments.filter(a => a.status === "Completed").length

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">A</div>
          <span>Appoint<span>HUB</span></span>
        </div>

        <p className="menu-label">MAIN MENU</p>
        <nav className="side-nav">
          <a className="nav-item active" href="#dashboard">▦ <span>Dashboard</span></a>
          <a className="nav-item" href="#appointments">▣ <span>Appointments</span></a>
          <a className="nav-item" href="#overview">◷ <span>Overview</span></a>
        </nav>

        <div className="sidebar-bottom">
          <div className="help-card">
            <span>💡</span>
            <strong>Need help?</strong>
            <small>Manage your appointments with ease.</small>
          </div>
          <div className="profile">
            <div className="avatar">A</div>
            <div>
              <strong>Administrator</strong>
              <small>AppointHUB Admin</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="dashboard-main" id="dashboard">
        <header className="topbar">
          <div>
            <h2>Dashboard</h2>
            <p>Manage and track your appointments</p>
          </div>
          <div className="topbar-right">
            <span className="today-label">📅 {today}</span>
            <div className="top-avatar">A</div>
          </div>
        </header>

        <section className="welcome-section">
          <div>
            <h1>Welcome back, Admin! 👋</h1>
            <p>Here's what's happening with your appointments today.</p>
          </div>
          <button className="primary-btn" onClick={() => {
            setEditingId(null)
            setForm(emptyForm)
            setShowForm(true)
          }}>
            + New Appointment
          </button>
        </section>

        {message && <div className="success-message">{message}</div>}
        {error && <div className="error">{error}</div>}

        <section className="stats-grid" id="overview">
          <div className="stat-card">
            <div className="stat-icon purple">▣</div>
            <p>Total Appointments</p>
            <h2>{appointments.length}</h2>
            <small>All recorded appointments</small>
          </div>
          <div className="stat-card">
            <div className="stat-icon orange">◷</div>
            <p>Pending</p>
            <h2>{pending}</h2>
            <small>Waiting for confirmation</small>
          </div>
          <div className="stat-card">
            <div className="stat-icon green">✓</div>
            <p>Confirmed</p>
            <h2>{confirmed}</h2>
            <small>Confirmed appointments</small>
          </div>
          <div className="stat-card">
            <div className="stat-icon blue">▤</div>
            <p>Completed</p>
            <h2>{completed}</h2>
            <small>Successfully completed</small>
          </div>
        </section>

        {showForm && (
          <section className="form-card">
            <div className="section-heading">
              <div>
                <h2>{editingId ? "Edit Appointment" : "Create New Appointment"}</h2>
                <p>Fill in the details below.</p>
              </div>
              <button className="close-btn" onClick={cancelForm}>✕</button>
            </div>

            <form onSubmit={handleSubmit} className="appointment-form">
              <label>Customer Name
                <input name="customer_name" value={form.customer_name}
                  onChange={handleChange} placeholder="Enter customer name" required />
              </label>
              <label>Provider Name
                <input name="provider_name" value={form.provider_name}
                  onChange={handleChange} placeholder="Enter provider name" required />
              </label>
              <label>Appointment Date
                <input type="date" name="appointment_date"
                  value={form.appointment_date} onChange={handleChange} required />
              </label>
              <label>Appointment Time
                <input type="time" name="appointment_time"
                  value={form.appointment_time} onChange={handleChange} required />
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
                <button type="submit" className="primary-btn">
                  {editingId ? "Save Changes" : "Create Appointment"}
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="appointments-section" id="appointments">
          <div className="section-heading">
            <div>
              <h2>Recent Appointments</h2>
              <p>View and manage all your appointments.</p>
            </div>
            <button className="secondary-btn" onClick={() => void loadAppointments()}>
              ↻ Refresh
            </button>
          </div>

          <div className="table-toolbar">
            <input
              className="search-input"
              placeholder="Search customer or provider..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <select value={filter} onChange={e => setFilter(e.target.value)}>
              <option>All</option>
              <option>Pending</option>
              <option>Confirmed</option>
              <option>Completed</option>
              <option>Cancelled</option>
            </select>
          </div>

          {loading ? <p>Loading appointments...</p> :
            filteredAppointments.length === 0 ? (
              <div className="empty-state">
                <div>▣</div>
                <h3>No appointments found</h3>
                <p>Create an appointment or change your search.</p>
              </div>
            ) : (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Customer</th>
                      <th>Provider</th>
                      <th>Date & Time</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredAppointments.map(appointment => (
                      <tr key={appointment.id}>
                        <td>
                          <strong>{appointment.customer_name}</strong>
                          <small>Appointment #{appointment.id}</small>
                        </td>
                        <td>{appointment.provider_name}</td>
                        <td>
                          {appointment.appointment_date}
                          <small>{appointment.appointment_time}</small>
                        </td>
                        <td>
                          <span className={`status-badge ${appointment.status.toLowerCase()}`}>
                            {appointment.status}
                          </span>
                        </td>
                        <td>
                          <div className="action-buttons">
                            <button className="view-action" onClick={() => void viewAppointment(appointment.id)}>View</button>
                            <button className="edit-action" onClick={() => editAppointment(appointment)}>Edit</button>
                            <button className="delete-action" onClick={() => void deleteAppointment(appointment.id)}>Delete</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        </section>

        {selected && (
          <div className="modal-backdrop" onClick={() => setSelected(null)}>
            <div className="details-modal" onClick={e => e.stopPropagation()}>
              <div className="section-heading">
                <h2>Appointment Details</h2>
                <button className="close-btn" onClick={() => setSelected(null)}>✕</button>
              </div>
              <p><strong>Appointment ID:</strong> #{selected.id}</p>
              <p><strong>Customer:</strong> {selected.customer_name}</p>
              <p><strong>Provider:</strong> {selected.provider_name}</p>
              <p><strong>Date:</strong> {selected.appointment_date}</p>
              <p><strong>Time:</strong> {selected.appointment_time}</p>
              <p><strong>Status:</strong> {selected.status}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
