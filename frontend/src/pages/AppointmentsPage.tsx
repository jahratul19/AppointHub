
import type { Appointment, AppointmentForm } from "../types"
import type { FormEvent, ChangeEvent } from "react"
import AppointmentTable from "../components/AppointmentTable"

type AppointmentsPageProps = {
  form: AppointmentForm
  editingId: number | null
  showForm: boolean
  loading: boolean
  search: string
  filter: string
  filteredAppointments: Appointment[]
  onNewAppointment: () => void
  onCancelForm: () => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
  onChange: (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => void
  onSearchChange: (value: string) => void
  onFilterChange: (value: string) => void
  onRefresh: () => void
  onView: (id: number) => void
  onEdit: (appointment: Appointment) => void
  onDelete: (id: number) => void
}

export default function AppointmentsPage({
  form,
  editingId,
  showForm,
  loading,
  search,
  filter,
  filteredAppointments,
  onNewAppointment,
  onCancelForm,
  onSubmit,
  onChange,
  onSearchChange,
  onFilterChange,
  onRefresh,
  onView,
  onEdit,
  onDelete,
}: AppointmentsPageProps) {
  return (
    <>
      <section className="welcome-section">
        <div>
          <span className="eyebrow">SCHEDULE MANAGEMENT</span>
          <h1>Manage your appointments.</h1>
          <p>
            Create, update, view, and organize your appointments.
          </p>
        </div>

        <button className="primary-btn" onClick={onNewAppointment}>
          ＋ New appointment
        </button>
      </section>

      {showForm && (
        <section className="form-card">
          <div className="section-heading">
            <div>
              <span className="eyebrow">APPOINTMENT DETAILS</span>
              <h2>
                {editingId ? "Edit appointment" : "Create new appointment"}
              </h2>
              <p>Enter the information below.</p>
            </div>

            <button className="close-btn" onClick={onCancelForm}>
              ✕
            </button>
          </div>

          <form onSubmit={onSubmit} className="appointment-form">
            <label>
              Customer name
              <input
                name="customer_name"
                value={form.customer_name}
                onChange={onChange}
                placeholder="Enter customer name"
                required
              />
            </label>

            <label>
              Provider name
              <input
                name="provider_name"
                value={form.provider_name}
                onChange={onChange}
                placeholder="Enter provider name"
                required
              />
            </label>

            <label>
              Appointment date
              <input
                type="date"
                name="appointment_date"
                value={form.appointment_date}
                onChange={onChange}
                required
              />
            </label>

            <label>
              Appointment time
              <input
                type="time"
                name="appointment_time"
                value={form.appointment_time}
                onChange={onChange}
                required
              />
            </label>

            <label>
              Status
              <select name="status" value={form.status} onChange={onChange}>
                <option>Pending</option>
                <option>Confirmed</option>
                <option>Completed</option>
                <option>Cancelled</option>
              </select>
            </label>

            <div className="form-actions">
              <button
                type="button"
                className="secondary-btn"
                onClick={onCancelForm}
              >
                Cancel
              </button>

              <button type="submit" className="primary-btn">
                {editingId ? "Save changes" : "Create appointment"}
              </button>
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

          <button className="secondary-btn" onClick={onRefresh}>
            ↻ Refresh
          </button>
        </div>

        <div className="table-toolbar">
          <input
            className="search-input"
            placeholder="Search customer or provider..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
          />

          <select
            value={filter}
            onChange={(e) => onFilterChange(e.target.value)}
          >
            <option>All</option>
            <option>Pending</option>
            <option>Confirmed</option>
            <option>Completed</option>
            <option>Cancelled</option>
          </select>
        </div>

        {loading ? (
          <p className="empty-state">Loading appointments...</p>
        ) : filteredAppointments.length === 0 ? (
          <div className="empty-state">
            <div>▤</div>
            <h3>No appointments found</h3>
            <p>Create an appointment or change your search.</p>
          </div>
        ) : (
          <AppointmentTable
            items={filteredAppointments}
            onView={onView}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        )}
      </section>
    </>
  )
}
