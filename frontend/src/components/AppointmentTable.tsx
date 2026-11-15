import type { Appointment } from "../types"

type AppointmentTableProps = {
  items: Appointment[]
  onView: (id: number) => void
  onEdit: (appointment: Appointment) => void
  onDelete: (id: number) => void
}

export default function AppointmentTable({
  items,
  onView,
  onEdit,
  onDelete,
}: AppointmentTableProps) {
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
          {items.map((appointment) => (
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
                  <button
                    className="view-action"
                    onClick={() => onView(appointment.id)}
                  >
                    View
                  </button>

                  <button
                    className="edit-action"
                    onClick={() => onEdit(appointment)}
                  >
                    Edit
                  </button>

                  <button
                    className="delete-action"
                    onClick={() => onDelete(appointment.id)}
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
