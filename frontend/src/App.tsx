import { useEffect, useRef, useState } from 'react'
import './App.css'
import { supabase, supabaseConfigured } from './lib/supabase'
import { formatDate } from './utils/formatDate'

type Note = {
  id: string
  title: string
  content: string
  created_at: string
  updated_at: string
}

type ChatMessage = {
  role: 'user' | 'ai'
  text: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function App() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('demo@example.com')
  const [password, setPassword] = useState('secret123')
  const [token, setToken] = useState<string | null>(null)
  const [notes, setNotes] = useState<Note[]>([])
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [status, setStatus] = useState('Ready')
  const [chatQuestion, setChatQuestion] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  const chatBodyRef = useRef<HTMLDivElement>(null)

  const loadNotes = async (currentToken = token) => {
    if (!currentToken) {
      setStatus('Log in to view notes')
      return
    }

    try {
      const response = await fetch(`${API_BASE}/notes`, {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
      const data = await response.json()

      if (!response.ok) {
        throw new Error(JSON.stringify(data))
      }

      setNotes(data)
      if (!data.length) {
        setSelectedNoteId(null)
        setTitle('')
        setContent('')
      }
      setStatus(`Loaded ${data.length} note(s)`)
    } catch (error) {
      setStatus(`Could not load notes: ${String(error)}`)
      console.error(error)
    }
  }

  useEffect(() => {
    let mounted = true

    void supabase.auth.getSession().then(({ data: { session } }) => {
      if (mounted) {
        setToken(session?.access_token ?? null)
      }
    })

    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setToken(session?.access_token ?? null)
    })

    return () => {
      mounted = false
      data.subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    if (token) {
      void loadNotes(token)
    }
  }, [token])

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight
    }
  }, [chatMessages, chatLoading])

  const resetForm = () => {
    setSelectedNoteId(null)
    setTitle('')
    setContent('')
  }

  const handleAuth = async () => {
    if (!supabaseConfigured) {
      setStatus('Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to frontend/.env')
      return
    }

    try {
      const result = mode === 'login'
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password })

      if (result.error) {
        throw result.error
      }

      if (mode === 'login') {
        setStatus('Login successful.')
      } else {
        setStatus(result.data.session ? 'Registration successful.' : 'Registration successful. Check your email to confirm your account.')
      }
    } catch (error) {
      setStatus(`Auth failed: ${String(error)}`)
      console.error(error)
    }
  }

  const handleSaveNote = async () => {
    if (!token) {
      setStatus('Log in first')
      return
    }

    try {
      const url = `${API_BASE}/notes${selectedNoteId ? `/${selectedNoteId}` : ''}`
      const method = selectedNoteId ? 'PUT' : 'POST'
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ title, content }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(JSON.stringify(data))
      }

      setStatus(selectedNoteId ? 'Note updated.' : 'Note created.')
      resetForm()
      await loadNotes(token)
    } catch (error) {
      setStatus(`Save failed: ${String(error)}`)
      console.error(error)
    }
  }

  const handleSelectNote = (note: Note) => {
    setSelectedNoteId(note.id)
    setTitle(note.title)
    setContent(note.content)
  }

  const handleDeleteNote = async (noteId: string) => {
    if (!token) return

    try {
      const response = await fetch(`${API_BASE}/notes/${noteId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(JSON.stringify(data))
      }

      setStatus('Note deleted.')
      resetForm()
      await loadNotes(token)
    } catch (error) {
      setStatus(`Delete failed: ${String(error)}`)
      console.error(error)
    }
  }

  const handleAskQuestion = async () => {
    if (!token || !chatQuestion.trim()) {
      return
    }

    const question = chatQuestion.trim()
    setChatMessages((prev) => [...prev, { role: 'user', text: question }])
    setChatQuestion('')
    setChatLoading(true)
    setStatus('Asking your notes...')

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(JSON.stringify(data))
      }

      const answer = data.answer ?? 'No answer returned.'
      setChatMessages((prev) => [...prev, { role: 'ai', text: answer }])
      setStatus('Question answered.')
    } catch (error) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'ai', text: `Something went wrong: ${String(error)}` },
      ])
      setStatus(`Chat failed: ${String(error)}`)
      console.error(error)
    } finally {
      setChatLoading(false)
    }
  }

  const handleChatKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void handleAskQuestion()
    }
  }

  const handleLogout = () => {
    void supabase.auth.signOut()
    setToken(null)
    resetForm()
    setNotes([])
    setChatQuestion('')
    setChatMessages([])
    setStatus('Logged out. Please log in again.')
  }

  const selectedNote = notes.find((note) => note.id === selectedNoteId) ?? null

  /* ─── Auth Screen ─────────────────────────────────────────────── */
  if (!token) {
    return (
      <main className="app-shell auth-shell">
        <section className="panel auth-panel" aria-label="Authentication">
          <div className="auth-brand">
            <div className="auth-logo" aria-hidden="true">✦</div>
            <h1>NoteAI</h1>
          </div>
          <p className="subtitle">Sign in to access your notes and AI-powered chat.</p>

          <div className="mode-toggle" role="group" aria-label="Auth mode">
            <button
              id="btn-login-tab"
              className={mode === 'login' ? 'selected' : ''}
              onClick={() => setMode('login')}
              type="button"
            >
              Login
            </button>
            <button
              id="btn-register-tab"
              className={mode === 'register' ? 'selected' : ''}
              onClick={() => setMode('register')}
              type="button"
            >
              Register
            </button>
          </div>

          <div className="stack">
            <label className="field-label" htmlFor="auth-email">
              Email
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
              />
            </label>

            <label className="field-label" htmlFor="auth-password">
              Password
              <input
                id="auth-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
            </label>

            <button id="btn-auth-submit" onClick={handleAuth} type="button">
              {mode === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          </div>

          <div className="status-bar" role="status" aria-live="polite">
            <div className="status-dot" />
            <pre>{status}</pre>
          </div>
        </section>
      </main>
    )
  }

  /* ─── Main App ────────────────────────────────────────────────── */
  return (
    <main className="app-shell notes-shell">

      {/* ── Sidebar ──────────────────────────────────────────────── */}
      <aside className="sidebar panel" aria-label="Notes list">
        <div className="sidebar-header">
          <div className="sidebar-logo" aria-hidden="true">✦</div>
          <h2>NoteAI</h2>
          {notes.length > 0 && (
            <span className="notes-count" aria-label={`${notes.length} notes`}>
              {notes.length}
            </span>
          )}
        </div>

        <button
          id="btn-new-note"
          className="new-note-btn"
          onClick={() => resetForm()}
          type="button"
        >
          <span aria-hidden="true">＋</span>
          New note
        </button>

        <ul className="note-list" role="list" aria-label="Your notes">
          {notes.length === 0 ? (
            <li className="empty-state">
              <div className="empty-state-icon" aria-hidden="true">📝</div>
              <p>No notes yet.<br />Create your first one!</p>
            </li>
          ) : (
            notes.map((note) => (
              <li
                key={note.id}
                className={`note-list-item${selectedNoteId === note.id ? ' selected-note' : ''}`}
              >
                <button
                  className="note-select-btn"
                  type="button"
                  onClick={() => handleSelectNote(note)}
                  aria-current={selectedNoteId === note.id ? 'true' : undefined}
                >
                  <strong>{note.title || 'Untitled note'}</strong>
                  <time dateTime={note.updated_at}>{formatDate(note.updated_at)}</time>
                </button>
                <button
                  className="delete-btn"
                  type="button"
                  onClick={() => handleDeleteNote(note.id)}
                  aria-label={`Delete "${note.title || 'Untitled note'}"`}
                  title="Delete note"
                >
                  🗑
                </button>
              </li>
            ))
          )}
        </ul>

        <button
          id="btn-logout"
          className="ghost-btn"
          onClick={handleLogout}
          type="button"
          style={{ width: '100%', marginTop: 'auto' }}
        >
          Sign out
        </button>
      </aside>

      {/* ── Editor ───────────────────────────────────────────────── */}
      <section className="panel editor-panel" aria-label="Note editor">
        <div className="editor-header">
          <h2>{selectedNoteId ? 'Edit note' : 'New note'}</h2>
          {selectedNote && (
            <div className="note-meta">
              <span>Created {formatDate(selectedNote.created_at)}</span>
              <span>Updated {formatDate(selectedNote.updated_at)}</span>
            </div>
          )}
        </div>

        <div className="stack">
          <label className="field-label" htmlFor="note-title">
            Title
            <input
              id="note-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Give your note a title…"
            />
          </label>

          <label className="field-label" htmlFor="note-content">
            Content
            <textarea
              id="note-content"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={14}
              placeholder="Start writing…"
            />
          </label>

          <div className="actions-row">
            <button id="btn-save-note" onClick={handleSaveNote} type="button">
              {selectedNoteId ? 'Save changes' : 'Create note'}
            </button>
            {selectedNoteId && (
              <button
                id="btn-cancel-edit"
                className="secondary-btn"
                onClick={resetForm}
                type="button"
              >
                Cancel
              </button>
            )}
          </div>
        </div>

        <div className="status-bar" role="status" aria-live="polite">
          <div className="status-dot" />
          <pre>{status}</pre>
        </div>
      </section>

      {/* ── Chat Panel ───────────────────────────────────────────── */}
      <section className="panel chat-panel" aria-label="AI Chat">
        <div className="chat-header">
          <div className="chat-icon" aria-hidden="true">✦</div>
          <h3>Ask your notes</h3>
        </div>

        <div className="chat-body" ref={chatBodyRef} aria-live="polite">
          {chatMessages.length === 0 && !chatLoading ? (
            <div className="chat-empty">
              <div className="chat-empty-icon" aria-hidden="true">💬</div>
              <p>Ask a question and the AI will answer using your notes as context.</p>
            </div>
          ) : (
            <>
              {chatMessages.map((msg, i) =>
                msg.role === 'user' ? (
                  <div key={i} className="chat-bubble chat-bubble-user">
                    {msg.text}
                  </div>
                ) : (
                  <div key={i} className="chat-bubble chat-bubble-ai">
                    <div className="ai-label">
                      <span aria-hidden="true">✦</span> NoteAI
                    </div>
                    {msg.text}
                  </div>
                )
              )}
              {chatLoading && (
                <div className="chat-thinking" aria-label="AI is thinking">
                  <div className="thinking-dots" aria-hidden="true">
                    <span /><span /><span />
                  </div>
                  Thinking…
                </div>
              )}
            </>
          )}
        </div>

        <div className="chat-input-area">
          <div className="chat-input-row">
            <textarea
              id="chat-question-input"
              value={chatQuestion}
              onChange={(e) => setChatQuestion(e.target.value)}
              onKeyDown={handleChatKeyDown}
              rows={2}
              placeholder="Ask about your notes… (Enter to send)"
              aria-label="Chat question"
            />
            <button
              id="btn-chat-send"
              className="send-btn"
              onClick={handleAskQuestion}
              type="button"
              disabled={chatLoading || !chatQuestion.trim()}
              aria-label="Send question"
              title="Send (Enter)"
            >
              ↑
            </button>
          </div>
        </div>
      </section>

    </main>
  )
}

export default App
