import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [session, setSession] = useState(null)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [images, setImages] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    // Check for session in URL
    const params = new URLSearchParams(window.location.search)
    const sessionId = params.get('session')

    if (sessionId) {
      setSession(sessionId)
      fetchProfile(sessionId)
    }
  }, [])

  const fetchProfile = async (sessionId) => {
    try {
      const response = await fetch(`/api/profile?session=${sessionId}`)
      if (!response.ok) throw new Error('Failed to fetch profile')
      const data = await response.json()
      setProfile(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleLogin = async () => {
    try {
      setLoading(true)
      const response = await fetch('/auth/login')
      const data = await response.json()
      window.location.href = data.auth_url
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    try {
      setGenerating(true)
      setError(null)

      const response = await fetch('/api/generate-headshots', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session }),
      })

      if (!response.ok) throw new Error('Failed to generate headshots')

      const data = await response.json()
      setImages(data.images)
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating(false)
    }
  }

  const handleDownload = async (imageId, style) => {
    try {
      const response = await fetch(`/api/image/${imageId}?session=${session}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `headshot_${style.replace(/\s+/g, '_')}.png`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError('Failed to download image')
    }
  }

  if (!session) {
    return (
      <div className="container">
        <div className="hero">
          <h1>LinkedIn Headshot Generator</h1>
          <p className="subtitle">
            Create professional headshots from your LinkedIn profile in seconds
          </p>
          <button
            className="btn-primary"
            onClick={handleLogin}
            disabled={loading}
          >
            {loading ? 'Connecting...' : 'Sign in with LinkedIn'}
          </button>
        </div>
      </div>
    )
  }

  if (profile && images.length === 0) {
    return (
      <div className="container">
        <div className="profile-section">
          <img
            src={profile.picture}
            alt={profile.name}
            className="profile-image"
          />
          <h2>Welcome, {profile.name}!</h2>
          <p className="subtitle">
            Ready to generate your professional headshots?
          </p>
          <button
            className="btn-primary"
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate Headshots'}
          </button>
          {error && <div className="error">{error}</div>}
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="results-section">
        <h2>Your Professional Headshots</h2>
        <p className="subtitle">Click any image to download</p>

        <div className="images-grid">
          {images.map((img) => (
            <div key={img.image_id} className="image-card">
              <div className="image-wrapper">
                {img.status === 'generated' ? (
                  <img
                    src={`/api/image/${img.image_id}?session=${session}`}
                    alt={img.style}
                    className="headshot-image"
                    onClick={() => handleDownload(img.image_id, img.style)}
                  />
                ) : (
                  <div className="image-error">
                    <p>Failed to generate</p>
                    <small>{img.error}</small>
                  </div>
                )}
              </div>
              <div className="image-footer">
                <h3>{img.style}</h3>
                {img.status === 'generated' && (
                  <button
                    className="btn-download"
                    onClick={() => handleDownload(img.image_id, img.style)}
                  >
                    Download PNG
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        <button
          className="btn-secondary"
          onClick={() => window.location.href = '/'}
        >
          Start Over
        </button>
      </div>
    </div>
  )
}

export default App
