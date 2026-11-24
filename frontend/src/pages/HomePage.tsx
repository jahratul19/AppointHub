import {
  Stethoscope,
  CalendarCheck,
  ClipboardList,
} from "lucide-react"

type HomePageProps = {
  onLogin: () => void
  onRegister: () => void
}

export default function HomePage({
  onLogin,
  onRegister,
}: HomePageProps) {
  return (
    <div className="home-page">
      <header className="home-navbar">
        <div className="home-brand">
          <Stethoscope size={27} />
          <span>Appoint<span>HUB</span></span>
        </div>

        <div className="home-nav-actions">
          <button onClick={onLogin} className="home-login-btn">
            Login
          </button>
          <button onClick={onRegister} className="home-register-btn">
            Register
          </button>
        </div>
      </header>

      <main>
        <section className="home-hero">
          <div className="home-hero-content">
            <span className="home-tag">
              YOUR HEALTH, OUR PRIORITY
            </span>

            <h1>
              Welcome to
              <br />
              Appoint<span>HUB</span>
            </h1>

            <p>
              Book appointments, connect with trusted doctors,
              and manage your healthcare journey — all in one place.
            </p>

            <button
              className="home-get-started"
              onClick={onRegister}
            >
              Get Started
            </button>
          </div>

          <div className="home-hero-image">
            <img
              src="/appoint-hub-doctor-hero.png"
              alt="Doctor in a modern healthcare clinic"
            />
          </div>
        </section>

        <section className="home-how">
          <h2>How AppointHUB Works</h2>

          <div className="home-steps">
  <div>
    <Stethoscope size={28} />
    <h3>Care Discovery</h3>
    <p>Explore doctors and find the right healthcare professional.</p>
  </div>

  <div>
    <CalendarCheck size={28} />
    <h3>Smart Scheduling</h3>
    <p>Choose a suitable time and book your appointment.</p>
  </div>

  <div>
    <ClipboardList size={28} />
    <h3>Care Overview</h3>
    <p>Keep track of and manage your appointments in one place.</p>
  </div>
</div>
        </section>
      </main>
    </div>
  )
}