import {
  getAppointments,
  authenticate,
  saveAppointment,
  getAppointment,
  deleteAppointment as deleteAppointmentApi,
} from "./services/api"
import HelpPage from "./pages/HelpPage"
import AppointmentsPage from "./pages/AppointmentsPage"
import DashboardPage from "./pages/DashboardPage"
import AuthPage from "./pages/AuthPage"
import { useEffect, useState, type FormEvent, type ChangeEvent } from "react"
import AppointmentTable from "./components/AppointmentTable"
import type { Appointment, AppointmentForm, Page, AuthMode } from "./types"

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

  // AUTHENTICATION STATE
  const [token, setToken] = useState<string | null>(null)
  const [authMode, setAuthMode] = useState<AuthMode>("login")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [authLoading, setAuthLoading] = useState(false)

  async function loadAppointments() {
    setLoading(true)
    setError("")

    try {
      const response = await getAppointments()

      if (!response.ok) {
        throw new Error("Could not load appointments")
      }

      const data: Appointment[] = await response.json()
      setAppointments(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  // LOAD APPOINTMENTS AFTER LOGIN
  useEffect(() => {
    if (token) {
      void loadAppointments()
    }
  }, [token])

  // AUTHENTICATION
  async function handleAuthSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setMessage("")
    setAuthLoading(true)

    
    const payload =
  authMode === "register"
    ? { username, email, password }
    : { email, password }

try {
  const response = await authenticate(authMode, payload)

  const responseText = await response.text()
  const data = responseText ? JSON.parse(responseText) : {}
      if (!response.ok) {
        throw new Error(
          data.detail || "Authentication failed. Please try again."
        )
      }

      if (authMode === "register") {
        setMessage("Registration successful! Please log in.")
        setAuthMode("login")
        setUsername("")
        setPassword("")
      } else {
        setToken(data.access_token)
        setPassword("")
        setMessage("Login successful!")
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong"
      )
    } finally {
      setAuthLoading(false)
    }
  }

  function handleLogout() {
    setToken(null)
    setAppointments([])
    setSelected(null)
    setShowForm(false)
    setEditingId(null)
    setForm(emptyForm)
    setPage("overview")
    setMessage("You have logged out successfully.")
    setError("")
    setAuthMode("login")
  }

  function handleChange(
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  // APPOINTMENT CREATE AND UPDATE
  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setMessage("")

    if (!token) {
      setError("Please log in first.")
      return
    }

    const payload = {
      ...form,
      appointment_time:
        form.appointment_time.length === 5
          ? `${form.appointment_time}:00`
          : form.appointment_time,
    }

    try {
      const response = await saveAppointment(editingId, token, payload)

      if (!response.ok) {
        const responseText = await response.text()
        let errorMessage = "Request failed"

        if (responseText) {
          try {
            const detail = JSON.parse(responseText)
            errorMessage = detail.detail || errorMessage
          } catch {
            errorMessage = responseText
          }
        }

        throw new Error(errorMessage)
      }

      setMessage(
        editingId
          ? "Appointment updated successfully!"
          : "Appointment created successfully!"
      )

      setForm(emptyForm)
      setEditingId(null)
      setShowForm(false)
      setSelected(null)
      setPage("appointments")

      await loadAppointments()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong"
      )
    }
  }

  // VIEW APPOINTMENT
  async function viewAppointment(id: number) {
    setError("")

    try {
      const response = await getAppointment(id)

      if (!response.ok) {
        throw new Error("Appointment not found")
      }

      setSelected(await response.json())
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong"
      )
    }
  }

  // EDIT APPOINTMENT
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

  // DELETE APPOINTMENT
  async function deleteAppointment(id: number) {
    if (
      !window.confirm(
        "Are you sure you want to delete this appointment?"
      )
    ) {
      return
    }

    setError("")
    setMessage("")

    try {
      const response = await deleteAppointmentApi(id)

      if (!response.ok) {
        throw new Error("Could not delete appointment")
      }

      setMessage("Appointment deleted successfully!")
      setSelected(null)

      await loadAppointments()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong"
      )
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

  // AUTHENTICATION SCREEN
  if (!token) {
  return (
    <AuthPage
      authMode={authMode}
      username={username}
      email={email}
      password={password}
      authLoading={authLoading}
      message={message}
      error={error}
      onSubmit={handleAuthSubmit}
      onUsernameChange={setUsername}
      onEmailChange={setEmail}
      onPasswordChange={setPassword}
      onToggleMode={() => {
        setAuthMode(authMode === "login" ? "register" : "login")
        setError("")
        setMessage("")
      }}
    />
  )
}

  // DASHBOARD DATA
  const today = new Date().toISOString().slice(0, 10)

  const pending = appointments.filter(
    (a) => a.status === "Pending"
  ).length

  const confirmed = appointments.filter(
    (a) => a.status === "Confirmed"
  ).length

  const completed = appointments.filter(
    (a) => a.status === "Completed"
  ).length

  const filteredAppointments = appointments.filter((a) => {
    const matchesSearch =
      a.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      a.provider_name.toLowerCase().includes(search.toLowerCase())

    const matchesFilter =
      filter === "All" || a.status === filter

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
          <span>
            Appoint<span>HUB</span>
          </span>
        </div>

        <p className="menu-label">WORKSPACE</p>

        <nav className="side-nav">
          <button
            className={`nav-item ${
              page === "overview" ? "active" : ""
            }`}
            onClick={() => setPage("overview")}
          >
            <span className="nav-icon">⌂</span> Overview
          </button>

          <button
            className={`nav-item ${
              page === "appointments" ? "active" : ""
            }`}
            onClick={() => setPage("appointments")}
          >
            <span className="nav-icon">▤</span> Appointments
          </button>
        </nav>

        <div className="sidebar-bottom">
          <button
            className="help-card"
            onClick={() => setPage("help")}
          >
            <span className="help-icon">✦</span>
            <strong>Need help?</strong>
            <small>Find your way around AppointHUB.</small>
            <span className="help-link">
              Get assistance →
            </span>
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
            <span className="eyebrow">
              APPOINTHUB WORKSPACE
            </span>
            <h2>
              {page === "overview"
                ? "Your workspace"
                : page === "appointments"
                  ? "Appointments"
                  : "Help center"}
            </h2>
          </div>

          <div className="topbar-right">
            <span className="today-label">
              ◷ &nbsp;{today}
            </span>
            <div className="top-avatar">A</div>
            <button
              className="logout-btn"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </header>

        {message && (
          <div className="success-message">{message}</div>
        )}

        {error && <div className="error">{error}</div>}

        {/* OVERVIEW PAGE */}
        {page === "overview" && (
  <DashboardPage
    appointments={appointments}
    pending={pending}
    confirmed={confirmed}
    completed={completed}
    recentAppointments={recentAppointments}
    loading={loading}
    onNewAppointment={openNewForm}
    onView={viewAppointment}
    onEdit={editAppointment}
    onDelete={deleteAppointment}
    onViewAll={() => setPage("appointments")}
  />
)}
        {/* APPOINTMENTS PAGE */}
        {page === "appointments" && (
  <AppointmentsPage
    form={form}
    editingId={editingId}
    showForm={showForm}
    loading={loading}
    search={search}
    filter={filter}
    filteredAppointments={filteredAppointments}
    onNewAppointment={openNewForm}
    onCancelForm={cancelForm}
    onSubmit={handleSubmit}
    onChange={handleChange}
    onSearchChange={setSearch}
    onFilterChange={setFilter}
    onRefresh={() => void loadAppointments()}
    onView={viewAppointment}
    onEdit={editAppointment}
    onDelete={deleteAppointment}
  />
)}

        {/* HELP PAGE */}
        {page === "help" && (
  <HelpPage
    onNewAppointment={openNewForm}
    onOpenAppointments={() => setPage("appointments")}
  />
)}
      </main>

      {/* APPOINTMENT DETAILS MODAL */}
      {selected && (
        <div
          className="modal-backdrop"
          onClick={() => setSelected(null)}
        >
          <div
            className="details-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="section-heading">
              <div>
                <span className="eyebrow">
                  RECORD #{selected.id}
                </span>
                <h2>Appointment details</h2>
              </div>

              <button
                className="close-btn"
                onClick={() => setSelected(null)}
              >
                ✕
              </button>
            </div>

            <p>
              <strong>Customer:</strong> {selected.customer_name}
            </p>
            <p>
              <strong>Provider:</strong> {selected.provider_name}
            </p>
            <p>
              <strong>Date:</strong> {selected.appointment_date}
            </p>
            <p>
              <strong>Time:</strong> {selected.appointment_time}
            </p>
            <p>
              <strong>Status:</strong> {selected.status}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

