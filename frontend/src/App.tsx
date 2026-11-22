import {
  getAppointments,
  authenticate,
  saveAppointment,
  getAppointment,
  deleteAppointment as deleteAppointmentApi,
  refreshAccessToken,
  logout as logoutApi,
  updateProfile,
  changePassword,
  getAdminDashboardStats,
  getAdminUsers,
  banAdminUser,
  unbanAdminUser,

} from "./services/api"

import HelpPage from "./pages/HelpPage"
import AppointmentsPage from "./pages/AppointmentsPage"
import DashboardPage from "./pages/DashboardPage"
import AuthPage from "./pages/AuthPage"
import { useEffect, useState, type FormEvent, type ChangeEvent } from "react"
import AppointmentTable from "./components/AppointmentTable"
import type { Appointment, AppointmentForm, Page, AuthMode } from "./types"
import { Eye, EyeOff } from "lucide-react"

const emptyForm: AppointmentForm = {
  customer_name: "",
  provider_name: "",
  appointment_date: "",
  appointment_time: "",
  status: "Pending",

}

function getRoleFromToken(token: string): string {
  try {
    const payload = token.split(".")[1]
    const normalized = payload
      .replace(/-/g, "+")
      .replace(/_/g, "/")

    const padded = normalized.padEnd(
      normalized.length + (4 - normalized.length % 4) % 4,
      "="
    )

    const decoded = JSON.parse(atob(padded))

    return typeof decoded.role === "string"
      ? decoded.role
      : "user"
  } catch {
    return "user"
  }
}

type AdminDashboardStats = {
  total_users: number
  banned_users: number
  total_appointments: number
  pending_appointments: number
}

type AdminUser = {
  id: number
  username: string
  email: string
  role: string
  is_banned: boolean
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
  const [adminUserFilter, setAdminUserFilter] = useState<
  "all" | "banned"
>("all")

const [adminAppointmentFilter, setAdminAppointmentFilter] =
  useState<"all" | "pending">("all")

  // AUTHENTICATION STATE
  const [token, setToken] = useState<string | null>(null)
  const [userRole, setUserRole] = useState<string>("user")
  const [adminStats, setAdminStats] =
  useState<AdminDashboardStats | null>(null)
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([])
  const [usersLoading, setUsersLoading] = useState(false)
  const [actionUser, setActionUser] = useState<AdminUser | null>(null)
  const [actionReason, setActionReason] = useState("")
  const [actionLoading, setActionLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [authMode, setAuthMode] = useState<AuthMode>("login")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [authLoading, setAuthLoading] = useState(false)


  async function handleUserAction() {
  if (!actionUser || !actionReason.trim() || !token) {
    setActionMessage("Please enter a reason.")
    return
  }

  setActionLoading(true)
  setActionMessage("")

  try {
    const response = actionUser.is_banned
      ? await unbanAdminUser(token, actionUser.id, actionReason)
      : await banAdminUser(token, actionUser.id, actionReason)

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || "Action failed")
    }

    setAdminUsers((previousUsers) =>
      previousUsers.map((user) =>
        user.id === actionUser.id
          ? { ...user, is_banned: !user.is_banned }
          : user
      )
    )

    setActionMessage("User status updated successfully.")
    setActionUser(null)
    setActionReason("")
  } catch (error) {
    setActionMessage(
      error instanceof Error ? error.message : "Something went wrong."
    )
  } finally {
    setActionLoading(false)
  }
}

  async function loadAppointments() {
    setLoading(true)
    setError("")

    try {
      if (!token) return

      const response = await getAppointments(token)
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

  // PROFILE AND PASSWORD STATE

  const [profileUsername, setProfileUsername] = useState("")
  const [profileEmail, setProfileEmail] = useState("")
  const [currentPassword, setCurrentPassword] = useState("")
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [newPassword, setNewPassword] = useState("")
  const [showAccount, setShowAccount] = useState(false)

// RESTORE LOGIN SESSION AFTER PAGE RELOAD
useEffect(() => {
  async function restoreSession() {
    try {
      const response = await refreshAccessToken()

      if (response.ok) {
        const data = await response.json()
        setToken(data.access_token)
        setUserRole(getRoleFromToken(data.access_token))
      }
    } catch {
      // User stays logged out if session restoration fails.
    }
  }

  void restoreSession()
}, [])

  // LOAD APPOINTMENTS AFTER LOGIN
  useEffect(() => {
    if (token) {
      void loadAppointments()
    }
  }, [token])

  useEffect(() => {
  if (!token || userRole !== "admin") {
    setAdminStats(null)
    return
  }

  async function loadAdminStats() {
    try {
      const response = await getAdminDashboardStats(token!)

      if (!response.ok) {
        throw new Error("Failed to load admin statistics")
      }

      const data: AdminDashboardStats = await response.json()
      setAdminStats(data)
    } catch (error) {
      console.error("Admin statistics error:", error)
    }
  }

  void loadAdminStats()
}, [token, userRole])

useEffect(() => {
  if (!token || userRole !== "admin") {
    setAdminUsers([])
    return
  }

  async function loadAdminUsers() {
    setUsersLoading(true)

    try {
      const response = await getAdminUsers(token!)

      if (!response.ok) {
        throw new Error("Failed to load admin users")
      }

      const data: AdminUser[] = await response.json()
      setAdminUsers(data)
    } catch (error) {
      console.error("Admin users error:", error)
    } finally {
      setUsersLoading(false)
    }
  }

  void loadAdminUsers()
}, [token, userRole])

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
        setUserRole(getRoleFromToken(data.access_token))
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

    async function handleProfileUpdate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setMessage("")

    if (!token) return

    try {
      const response = await updateProfile(token, {
        username: profileUsername,
        email: profileEmail,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Profile update failed")
      }

      setMessage("Profile updated successfully!")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

    async function handlePasswordChange(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError("")
    setMessage("")

    if (!token) return

    try {
      const response = await changePassword(token, {
        current_password: currentPassword,
        new_password: newPassword,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Password change failed")
      }

      setMessage("Password changed successfully!")
      setCurrentPassword("")
      setNewPassword("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }
  
  function handleLogout() {
    setToken(null)
    setUserRole("user")
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
      if (!token) return

      const response = await getAppointment(id, token)

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
      if (!token) return

      const response = await deleteAppointmentApi(id, token)

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

  const filteredAdminUsers = adminUsers.filter((user) => {
  const matchesSearch =
    user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())

  const matchesStatus =
    statusFilter === "all" ||
    (statusFilter === "active" && !user.is_banned) ||
    (statusFilter === "banned" && user.is_banned)

  return matchesSearch && matchesStatus
})
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
                    <button
            className={`nav-item ${
              page === "admin-users" ? "active" : ""
            }`}
            onClick={() => setPage("admin-users")}
          >
            <span className="nav-icon">♙</span> Users
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
    onClick={() => {
      setShowAccount(!showAccount)
      setError("")
      setMessage("")
    }}
  >
    Account Settings
  </button>

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

        {/* ACCOUNT SETTINGS */}
{showAccount && (
  <div className="account-settings">
    <h2>Account Settings</h2>

    <h3>Update Profile</h3>
    <form className="account-form" onSubmit={handleProfileUpdate}>
      <input
        type="text"
        placeholder="New username"
        value={profileUsername}
        onChange={(e) => setProfileUsername(e.target.value)}
        required
      />

      <input
        type="email"
        placeholder="New email"
        value={profileEmail}
        onChange={(e) => setProfileEmail(e.target.value)}
        required
      />

      <button type="submit">Update Profile</button>
    </form>

    <h3>Change Password</h3>
<form className="account-form" onSubmit={handlePasswordChange}>
  <div className="password-field">
    <input
      type={showCurrentPassword ? "text" : "password"}
      placeholder="Current password"
      value={currentPassword}
      onChange={(e) => setCurrentPassword(e.target.value)}
      required
    />
    <button
  type="button"
  className="toggle-password"
  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
>
  {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
</button>
  </div>

  <div className="password-field">
    <input
      type={showNewPassword ? "text" : "password"}
      placeholder="New password"
      value={newPassword}
      onChange={(e) => setNewPassword(e.target.value)}
      required
    />
    <button
  type="button"
  className="toggle-password"
  onClick={() => setShowNewPassword(!showNewPassword)}
>
  {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
</button>
  </div>

  <button type="submit">Change Password</button>
</form>
  </div>
)}

        {/* OVERVIEW PAGE */}
        {page === "overview" && !showAccount && (
  userRole === "admin" ? (
    <div className="admin-dashboard">
      <h2>Admin Dashboard</h2>
      <p>System overview and statistics</p>

      {adminStats ? (
        <div className="admin-stats-grid">
          <div className="admin-stat-card">
            <h3>Total Users</h3>
            <p>{adminStats.total_users}</p>
          </div>

          <div className="admin-stat-card">
            <h3>Banned Users</h3>
            <p>{adminStats.banned_users}</p>
          </div>

          <div className="admin-stat-card">
            <h3>Total Appointments</h3>
            <p>{adminStats.total_appointments}</p>
          </div>

          <div className="admin-stat-card">
            <h3>Pending Appointments</h3>
            <p>{adminStats.pending_appointments}</p>
          </div>
        </div>
      ) : (
        <p>Loading admin statistics...</p>
      )}
    </div>
  ) : (
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
  )
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

{/* ADMIN USERS PAGE */}
{page === "admin-users" && (
  <div className="admin-users-page">
    <h2>Manage Users</h2>
    <div className="users-controls">
  <input
    type="text"
    placeholder="Search by username or email..."
    value={searchTerm}
    onChange={(e) => setSearchTerm(e.target.value)}
  />

  <select
    value={statusFilter}
    onChange={(e) => setStatusFilter(e.target.value)}
  >
    <option value="all">All Users</option>
    <option value="active">Active Users</option>
    <option value="banned">Banned Users</option>
  </select>
</div>
    <p>View and manage registered users.</p>

    {usersLoading ? (
      <p>Loading users...</p>
    ) : filteredAdminUsers.length === 0 ? (
      <p>No users found.</p>
    ) : (
      <div className="admin-users-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>

          <tbody>
            {filteredAdminUsers.map((user) => (
              <tr key={user.id}>
                <td>{user.id}</td>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>
                  {user.is_banned ? "Banned" : "Active"}
                </td>

                <td>
  {user.role !== "admin" && (
    <button
  className={user.is_banned ? "unban-user-btn" : "ban-user-btn"}
  onClick={() => {
    setActionUser(user)
    setActionReason("")
    setActionMessage("")
  }}
>
  {user.is_banned ? "Unban" : "Ban"}
</button>
  )}
</td>
              </tr>
            ))}
          </tbody>
        </table>

        {actionUser && (
  <div className="action-modal">
    <h3>
      {actionUser.is_banned ? "Unban User" : "Ban User"}
    </h3>

    <p>
      Enter a reason for this action.
    </p>

    <textarea
      value={actionReason}
      onChange={(e) => setActionReason(e.target.value)}
      placeholder="Write reason here..."
    />

    {actionMessage && <p>{actionMessage}</p>}

    <button
      onClick={handleUserAction}
      disabled={actionLoading || !actionReason.trim()}
    >
      {actionLoading ? "Processing..." : "Confirm"}
    </button>

    <button
      onClick={() => {
        setActionUser(null)
        setActionReason("")
        setActionMessage("")
      }}
    >
      Cancel
    </button>
  </div>
)}
      </div>
    )}
  </div>
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

