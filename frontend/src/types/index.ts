export type Appointment = {
  id: number
  customer_name: string
  provider_name: string
  doctor_id: number | null
  appointment_date: string
  appointment_time: string
  status: string
  reason: string | null
}

export type AppointmentForm = {
  doctor_id: string
  appointment_date: string
  appointment_time: string
  reason: string
  status: string
}

export type Doctor = {
  id: number
  name: string
  photo_url: string | null
  specialty: string
  description: string
  is_active: boolean
}

export type DoctorForm = Omit<Doctor, "id">

export type Page =
  | "overview"
  | "appointments"
  | "doctors"
  | "help"
  | "groups"
  | "admin-users"
  | "admin-doctors"
  | "admin-content"
  | "admin-security"
  | "admin-audit-logs"
export type AuthMode = "login" | "register"
