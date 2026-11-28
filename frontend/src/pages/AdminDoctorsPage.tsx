import { useEffect, useState, type ChangeEvent, type FormEvent } from "react"
import {
  createAdminDoctor,
  deactivateAdminDoctor,
  getAdminDoctors,
  updateAdminDoctor,
} from "../services/api"
import type { Doctor, DoctorForm } from "../types"

const emptyDoctor: DoctorForm = {
  name: "",
  photo_url: "",
  specialty: "",
  description: "",
  is_active: true,
}

type Props = { token: string }

export default function AdminDoctorsPage({ token }: Props) {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [form, setForm] = useState<DoctorForm>(emptyDoctor)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  async function loadDoctors() {
    setLoading(true)
    setError("")
    try {
      const response = await getAdminDoctors(token)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || "Could not load doctors")
      setDoctors(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load doctors")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDoctors()
  }, [token])

  function handleChange(
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) {
    const { name, value } = event.target
    setForm((previous) => ({
      ...previous,
      [name]: name === "is_active" ? value === "true" : value,
    }))
  }

  function startEdit(doctor: Doctor) {
    setEditingId(doctor.id)
    setForm({
      name: doctor.name,
      photo_url: doctor.photo_url ?? "",
      specialty: doctor.specialty,
      description: doctor.description,
      is_active: doctor.is_active,
    })
    setError("")
    setMessage("")
  }

  function resetForm() {
    setEditingId(null)
    setForm(emptyDoctor)
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setMessage("")
    try {
      const payload = {
        ...form,
        photo_url: form.photo_url?.trim() || null,
      }
      const response = editingId
        ? await updateAdminDoctor(token, editingId, payload)
        : await createAdminDoctor(token, payload)
      const data = await response.json()
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((item: { msg?: string }) => item.msg).join(", ")
          : data.detail
        throw new Error(detail || "Could not save doctor")
      }
      setMessage(editingId ? "Doctor updated." : "Doctor created.")
      resetForm()
      await loadDoctors()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save doctor")
    } finally {
      setSaving(false)
    }
  }

  async function deactivate(doctor: Doctor) {
    if (!window.confirm(`Deactivate ${doctor.name}? Existing appointments will remain.`)) return
    setError("")
    setMessage("")
    try {
      const response = await deactivateAdminDoctor(token, doctor.id)
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || "Could not deactivate doctor")
      setMessage(`${doctor.name} is now inactive.`)
      await loadDoctors()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not deactivate doctor")
    }
  }

  return (
    <section className="admin-users-page">
      <h2>Doctor directory</h2>
      <p>Create, update and deactivate doctors shown to patients.</p>
      {error && <p className="error" role="alert">{error}</p>}
      {message && <p className="success-message" role="status">{message}</p>}

      <form className="doctor-admin-form" onSubmit={(event) => void submit(event)}>
        <h3>{editingId ? "Edit doctor" : "Add a doctor"}</h3>
        <label>
          Doctor name
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            minLength={2}
            maxLength={120}
            required
          />
        </label>
        <label>
          Specialty
          <input
            name="specialty"
            value={form.specialty}
            onChange={handleChange}
            minLength={2}
            maxLength={120}
            required
          />
        </label>
        <label>
          Profile photo URL
          <input
            name="photo_url"
            type="url"
            value={form.photo_url ?? ""}
            onChange={handleChange}
            maxLength={1000}
            placeholder="https://example.com/photo.jpg"
          />
        </label>
        <label>
          Status
          <select
            name="is_active"
            value={String(form.is_active)}
            onChange={handleChange}
          >
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </label>
        <label className="doctor-description-field">
          Description
          <textarea
            name="description"
            value={form.description}
            onChange={handleChange}
            maxLength={4000}
            rows={4}
          />
        </label>
        <div className="doctor-admin-actions">
          <button type="submit" className="primary-btn" disabled={saving}>
            {saving ? "Saving..." : editingId ? "Save changes" : "Add doctor"}
          </button>
          {editingId !== null && (
            <button type="button" className="secondary-btn" onClick={resetForm}>
              Cancel edit
            </button>
          )}
        </div>
      </form>

      <h3>All doctors</h3>
      {loading ? (
        <p role="status">Loading doctors...</p>
      ) : doctors.length === 0 ? (
        <p>No doctors have been added.</p>
      ) : (
        <div className="admin-users-table">
          <table>
            <thead>
              <tr><th>Name</th><th>Specialty</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {doctors.map((doctor) => (
                <tr key={doctor.id}>
                  <td>{doctor.name}</td>
                  <td>{doctor.specialty}</td>
                  <td>{doctor.is_active ? "Active" : "Inactive"}</td>
                  <td>
                    <button type="button" className="secondary-btn" onClick={() => startEdit(doctor)}>
                      Edit
                    </button>
                    {doctor.is_active && (
                      <button type="button" className="danger-btn" onClick={() => void deactivate(doctor)}>
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
