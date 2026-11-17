
type HelpPageProps = {
  onNewAppointment: () => void
  onOpenAppointments: () => void
}

export default function HelpPage({
  onNewAppointment,
  onOpenAppointments,
}: HelpPageProps) {
  return (
    <section className="help-page">
      <span className="eyebrow">SUPPORT & GUIDANCE</span>
      <h1>How can we help?</h1>
      <p className="help-intro">
        A quick guide to using your AppointHUB workspace.
      </p>

      <div className="help-grid">
        <article className="help-item">
          <span>＋</span>
          <h3>Create an appointment</h3>
          <p>
            Open Appointments and select “New appointment”.
            Fill in the customer, provider, date, time, and
            status, then save.
          </p>
          <button className="text-btn" onClick={onNewAppointment}>
            Create appointment →
          </button>
        </article>

        <article className="help-item">
          <span>▤</span>
          <h3>View your appointments</h3>
          <p>
            Use the Appointments page to see all records.
            Search by customer or provider and filter by status.
          </p>
          <button className="text-btn" onClick={onOpenAppointments}>
            Open appointments →
          </button>
        </article>

        <article className="help-item">
          <span>✎</span>
          <h3>Update or delete</h3>
          <p>
            Use the Edit action to update a record or Delete
            to remove an appointment after confirmation.
          </p>
          <button className="text-btn" onClick={onOpenAppointments}>
            Manage records →
          </button>
        </article>

        <article className="help-item">
          <span>◉</span>
          <h3>Understand appointment status</h3>
          <p>
            Pending means awaiting confirmation. Confirmed
            means scheduled. Completed means finished.
            Cancelled means no longer scheduled.
          </p>
        </article>
      </div>
    </section>
  )
}
