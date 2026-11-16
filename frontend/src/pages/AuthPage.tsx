
import type { FormEvent } from "react"
import type { AuthMode } from "../types"

type AuthPageProps = {
  authMode: AuthMode
  username: string
  email: string
  password: string
  authLoading: boolean
  message: string
  error: string
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
  onUsernameChange: (value: string) => void
  onEmailChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onToggleMode: () => void
}

export default function AuthPage({
  authMode,
  username,
  email,
  password,
  authLoading,
  message,
  error,
  onSubmit,
  onUsernameChange,
  onEmailChange,
  onPasswordChange,
  onToggleMode,
}: AuthPageProps) {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="brand-icon">A</div>
          <h1>AppointHUB</h1>
          <p>YOUR APPOINTMENT MANAGEMENT PLATFORM</p>
        </div>

        <h2>
          {authMode === "login"
            ? "Welcome back"
            : "Create your account"}
        </h2>

        <p className="auth-description">
          {authMode === "login"
            ? "Sign in to access your workspace."
            : "Register to get started with AppointHUB."}
        </p>

        {message && (
          <div className="success-message">{message}</div>
        )}

        {error && <div className="error">{error}</div>}

        <form onSubmit={onSubmit} className="auth-form">
          {authMode === "register" && (
            <label>
              Username
              <input
                type="text"
                value={username}
                onChange={(e) => onUsernameChange(e.target.value)}
                placeholder="Enter your username"
                required
              />
            </label>
          )}

          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(e) => onEmailChange(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => onPasswordChange(e.target.value)}
              placeholder="Enter your password"
              required
              minLength={8}
            />
          </label>

          <button
            type="submit"
            className="primary-btn"
            disabled={authLoading}
          >
            {authLoading
              ? "Please wait..."
              : authMode === "login"
                ? "Sign in"
                : "Create account"}
          </button>
        </form>

        <div className="auth-switch">
          {authMode === "login"
            ? "Don't have an account? "
            : "Already have an account? "}

          <button type="button" onClick={onToggleMode}>
            {authMode === "login" ? "Register" : "Login"}
          </button>
        </div>
      </div>
    </div>
  )
}
