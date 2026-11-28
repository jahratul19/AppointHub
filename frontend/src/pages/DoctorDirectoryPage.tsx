import type { Doctor } from "../types"

type Props = {
  doctors: Doctor[]
  loading: boolean
  error: string
  onBook: (doctor: Doctor) => void
}

const doctorIllustrations = [
  { background: "#e5f4f2", skin: "#bd805f", hair: "#263746", coat: "#ffffff", scrubs: "#3d9b91", style: "long" },
  { background: "#e9effb", skin: "#8f5c43", hair: "#202a32", coat: "#ffffff", scrubs: "#527bb0", style: "short" },
  { background: "#f8eee3", skin: "#d29a76", hair: "#49332b", coat: "#fffdf9", scrubs: "#b86f54", style: "curly" },
  { background: "#e7f2eb", skin: "#c58d6c", hair: "#33433e", coat: "#ffffff", scrubs: "#4b8c70", style: "hijab" },
  { background: "#f3eafa", skin: "#a96f52", hair: "#342632", coat: "#fffefe", scrubs: "#8c68a8", style: "ponytail" },
  { background: "#e8f3f8", skin: "#d09b79", hair: "#493a34", coat: "#ffffff", scrubs: "#39839a", style: "beard" },
  { background: "#f7f0e2", skin: "#b87a58", hair: "#252d3b", coat: "#fffefa", scrubs: "#b58b45", style: "glasses" },
] as const

function DoctorIllustration({ name, variant }: { name: string; variant: number }) {
  const illustration = doctorIllustrations[variant % doctorIllustrations.length]
  const isHijab = illustration.style === "hijab"
  const isCurly = illustration.style === "curly"
  const hasBeard = illustration.style === "beard"
  const hasGlasses = illustration.style === "glasses"

  return (
    <svg
      className="doctor-photo doctor-illustration"
      viewBox="0 0 800 440"
      role="img"
      aria-label={`Illustrated doctor placeholder for ${name}`}
    >
      <rect width="800" height="440" rx="18" fill={illustration.background} />
      <circle cx="400" cy="220" r="205" fill="#ffffff" opacity=".28" />
      {isHijab ? (
        <path d="M292 224C282 103 324 53 400 53s118 50 108 171l-24 110H316z" fill={illustration.scrubs} />
      ) : (
        <path d="M319 180c-12-55 16-116 81-116s93 61 81 116l12 107H307z" fill={illustration.hair} />
      )}
      {illustration.style === "ponytail" && <circle cx="492" cy="111" r="31" fill={illustration.hair} />}
      <path d="M215 440c16-94 72-142 145-153l40 39 40-39c73 11 129 59 145 153z" fill={illustration.scrubs} />
      <path d="m360 291 40 35-48 114H249c17-77 54-126 111-149zm80 0-40 35 48 114h103c-17-77-54-126-111-149z" fill={illustration.coat} />
      <path d="M370 244h60v67l-30 27-30-27z" fill={illustration.skin} />
      <ellipse cx="400" cy="169" rx="72" ry="91" fill={illustration.skin} />
      <ellipse cx="327" cy="177" rx="10" ry="17" fill={illustration.skin} />
      <ellipse cx="473" cy="177" rx="10" ry="17" fill={illustration.skin} />
      {isHijab ? (
        <path d="M319 153c8-74 39-103 81-103s73 29 81 103c-28-32-53-45-81-45s-53 13-81 45z" fill={illustration.scrubs} />
      ) : (
        <>
          <path d="M327 151c-5-51 26-87 73-87s78 36 73 87c-23-26-47-37-73-37s-50 11-73 37z" fill={illustration.hair} />
          {illustration.style === "long" && <path d="M329 140c-17 37-8 107 7 147l17-4-4-127zm142 0c17 37 8 107-7 147l-17-4 4-127z" fill={illustration.hair} />}
          {isCurly && (
            <g fill={illustration.hair}>
              <circle cx="340" cy="91" r="20" /><circle cx="371" cy="70" r="22" />
              <circle cx="403" cy="66" r="22" /><circle cx="435" cy="73" r="22" />
              <circle cx="461" cy="98" r="20" />
            </g>
          )}
        </>
      )}
      <path d="M367 172q12-9 24 0m18 0q12-9 24 0" fill="none" stroke="#45352e" strokeWidth="5" strokeLinecap="round" />
      <ellipse cx="380" cy="184" rx="4" ry="5" fill="#24323a" />
      <ellipse cx="420" cy="184" rx="4" ry="5" fill="#24323a" />
      <path d="M400 190v21m-12 17q12 9 24 0" fill="none" stroke="#86553f" strokeWidth="4" strokeLinecap="round" />
      {hasBeard && <path d="M348 215q52 62 104 0l-10 42q-42 38-84 0z" fill={illustration.hair} />}
      {hasGlasses && (
        <g fill="none" stroke="#32424a" strokeWidth="4">
          <circle cx="380" cy="184" r="20" /><circle cx="420" cy="184" r="20" />
          <path d="M400 183h-1m-39 0h-9m89 0h9" />
        </g>
      )}
      <path d="M400 350v55m0-47c-32 0-35 47 0 47s32-47 0-47" fill="none" stroke="#566f78" strokeWidth="7" strokeLinecap="round" />
      <circle cx="400" cy="407" r="8" fill="#566f78" />
      <path d="m360 291 40 35 40-35" fill="none" stroke="#d7e3e3" strokeWidth="7" />
      <rect x="454" y="350" width="27" height="35" rx="4" fill="#d8e6e5" />
    </svg>
  )
}

export default function DoctorDirectoryPage({
  doctors,
  loading,
  error,
  onBook,
}: Props) {
  return (
    <section className="doctor-directory">
      <header className="doctor-directory-header">
        <span className="eyebrow">OUR CARE TEAM</span>
        <h1>Find a doctor</h1>
        <p>Browse our available specialists and book a time that works for you.</p>
      </header>

      {error && <p className="error" role="alert">{error}</p>}
      {loading ? (
        <p className="empty-state" role="status">Loading doctors...</p>
      ) : doctors.length === 0 ? (
        <div className="empty-state">
          <h3>No doctors are available right now</h3>
          <p>Please check back later.</p>
        </div>
      ) : (
        <div className="doctor-grid">
          {doctors.map((doctor, index) => (
            <article className="doctor-card" key={doctor.id}>
              {doctor.photo_url ? (
                <img
                  className="doctor-photo"
                  src={doctor.photo_url}
                  alt={doctor.name}
                  loading="lazy"
                />
              ) : (
                <DoctorIllustration name={doctor.name} variant={index} />
              )}
              <div className="doctor-card-content">
                <span className="doctor-specialty">{doctor.specialty}</span>
                <h2>{doctor.name}</h2>
                <p>{doctor.description || "Contact us to learn more about this specialist."}</p>
                <button
                  type="button"
                  className="primary-btn"
                  onClick={() => onBook(doctor)}
                >
                  Book appointment
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
