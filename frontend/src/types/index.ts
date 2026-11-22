export type Appointment = {
  id: number
  customer_name: string
  provider_name: string
  appointment_date: string
  appointment_time: string
  status: string
}

export type AppointmentForm = {
  customer_name: string
  provider_name: string
  appointment_date: string
  appointment_time: string
  status: string
}

export type Page = "overview" | "appointments" | "help" | "admin-users"
export type AuthMode = "login" | "register"
