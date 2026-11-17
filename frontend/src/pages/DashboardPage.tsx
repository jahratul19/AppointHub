
import type { Appointment } from "../types"
import AppointmentTable from "../components/AppointmentTable"

type DashboardPageProps = {
  appointments: Appointment[]
  pending: number
  confirmed: number
  completed: number
  recentAppointments: Appointment[]
  loading: boolean
  onNewAppointment: () => void
  onView: (id: number) => void
  onEdit: (appointment: Appointment) => void
  onDelete: (id: number) => void
  onViewAll: () => void
}

export default function DashboardPage({
  appointments,
  pending,
  confirmed,
  completed,
  recentAppointments,
  loading,
  onNewAppointment,
  onView,
  onEdit,
  onDelete,
  onViewAll,
}: DashboardPageProps) {
  return (
    <>
      <section className="welcome-section">
        <div>
          <span className="eyebrow">YOUR DAILY SNAPSHOT</span>
          <h1>Everything in one place.</h1>
          <p>
            Keep track of your schedule and stay on top
            of every appointment.
          </p>
        </div>

        <button className="primary-btn" onClick={onNewAppointment}>
          ＋ New appointment
        </button>
      </section>

      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-top">
            <span>Total appointments</span>
            <span className="stat-icon purple">▤</span>
          </div>
          <h2>{appointments.length}</h2>
          <small>All recorded appointments</small>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span>Pending</span>
            <span className="stat-icon orange">◷</span>
          </div>
          <h2>{pending}</h2>
          <small>Waiting for confirmation</small>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span>Confirmed</span>
            <span className="stat-icon green">✓</span>
          </div>
          <h2>{confirmed}</h2>
          <small>Ready for appointment</small>
        </div>

        <div className="stat-card">
          <div className="stat-top">
            <span>Completed</span>
            <span className="stat-icon blue">▣</span>
          </div>
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

          <button className="secondary-btn" onClick={onViewAll}>
            View all →
          </button>
        </div>

        {loading ? (
          <p className="empty-state">Loading appointments...</p>
        ) : recentAppointments.length === 0 ? (
          <div className="empty-state">
            <div>▤</div>
            <h3>Your schedule is clear</h3>
            <p>Create your first appointment to get started.</p>
            <button className="primary-btn" onClick={onNewAppointment}>
              ＋ Create appointment
            </button>
          </div>
        ) : (
          <AppointmentTable
            items={recentAppointments}
            onView={onView}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        )}
      </section>
    </>
  )
}
