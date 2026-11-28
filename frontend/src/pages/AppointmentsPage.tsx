
import type { Appointment, AppointmentForm, Doctor } from "../types"
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
  doctors: Doctor[]
  doctorsLoading: boolean
  doctorError: string
  onNewAppointment: () => void
  onCancelForm: () => void
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
  onChange: (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => void
  onSearchChange: (value: string) => void
  onFilterChange: (value: string) => void
  onRefresh: () => void
  onView: (id: number) => void
  onEdit: (appointment: Appointment) => void
  onDelete: (id: number) => void
  onBrowseDoctors: () => void
}

export default function AppointmentsPage({
  form,
  editingId,
  showForm,
  loading,
  search,
  filter,
  filteredAppointments,
  doctors,
  doctorsLoading,
  doctorError,
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
  onBrowseDoctors,
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

      {doctorError && <p className="error" role="alert">{doctorError}</p>}

      {showForm && (
        <section className="form-card">
          <div className="section-heading">
            <div>
              <span className="eyebrow">APPOINTMENT DETAILS</span>
              <h2>
                {editingId ? "Edit appointment" : "Create new appointment"}
              </h2>
              <p>Select a doctor, date and time, and tell us what you need help with.</p>
            </div>

            <button className="close-btn" onClick={onCancelForm}>
              ✕
            </button>
          </div>

          <form onSubmit={onSubmit} className="appointment-form">
            <label>
              Doctor
              <select
                name="doctor_id"
                value={form.doctor_id}
                onChange={onChange}
                required
                disabled={doctorsLoading || doctors.length === 0}
              >
                <option value="">
                  {doctorsLoading ? "Loading doctors..." : "Select a doctor"}
                </option>
                {doctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    {doctor.name} — {doctor.specialty}
                  </option>
                ))}
              </select>
              <button type="button" className="text-button" onClick={onBrowseDoctors}>
                Browse doctor profiles
              </button>
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

            <label className="appointment-reason-field">
              Reason for visit
              <textarea
                name="reason"
                value={form.reason}
                onChange={onChange}
                placeholder="Briefly describe the reason for your visit"
                minLength={3}
                maxLength={2000}
                rows={4}
                required
              />
            </label>

            {editingId !== null && <label>
              Status
              <select name="status" value={form.status} onChange={onChange}>
                <option>Pending</option>
                <option>Confirmed</option>
                <option>Completed</option>
                <option>Cancelled</option>
              </select>
            </label>}

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
