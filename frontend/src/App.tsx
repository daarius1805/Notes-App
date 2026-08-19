import { useEffect, useState } from 'react'
import './App.css'
import { formatDate } from './utils/formatDate'

type Note = {
  id: string
  title: string
  content: string
  created_at: string
  updated_at: string
}

type Source = {
  note_id: string
  title: string
  chunk_text: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function App() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('demo@example.com')
  const [password, setPassword] = useState('secret123')
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('notes_app_token'))
  const [notes, setNotes] = useState<Note[]>([])
  const [selectedNoteId, setSelectedNoteId] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [status, setStatus] = useState('Ready')
  const [chatQuestion, setChatQuestion] = useState('')
  const [chatAnswer, setChatAnswer] = useState('')
  const [chatSources, setChatSources] = useState<Source[]>([])
  const [chatLoading, setChatLoading] = useState(false)

  const setAuthToken = (nextToken: string | null) => {
    if (nextToken) {
      localStorage.setItem('notes_app_token', nextToken)
    } else {
      localStorage.removeItem('notes_app_token')
    }
    setToken(nextToken)
  }

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
    if (token) {
      void loadNotes(token)
    }
  }, [token])

  const resetForm = () => {
    setSelectedNoteId(null)
    setTitle('')
    setContent('')
  }

  const handleAuth = async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(JSON.stringify(data))
      }

      if (mode === 'login') {
        setAuthToken(data.access_token)
        setStatus('Login successful. Token received.')
      } else {
        setStatus('Registration successful. You can now log in.')
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

    setChatLoading(true)
    setStatus('Asking your notes...')

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question: chatQuestion.trim() }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(JSON.stringify(data))
      }

      setChatAnswer(data.answer ?? 'No answer returned.')
      setChatSources(Array.isArray(data.sources) ? data.sources : [])
      setStatus('Question answered.')
      setChatQuestion('')
    } catch (error) {
      setChatAnswer('')
      setChatSources([])
      setStatus(`Chat failed: ${String(error)}`)
      console.error(error)
    } finally {
      setChatLoading(false)
    }
  }

  const handleLogout = () => {
    setAuthToken(null)
    resetForm()
    setNotes([])
    setChatQuestion('')
    setChatAnswer('')
    setChatSources([])
    setStatus('Logged out. Please log in again.')
  }

  const selectedNote = notes.find((note) => note.id === selectedNoteId) ?? null

  if (!token) {
    return (
      <main className="app-shell auth-shell">
        <section className="panel auth-panel">
          <h1>Notes App + RAG Bot</h1>
          <p className="subtitle">Please log in to access your notes.</p>

          <div className="mode-toggle">
            <button className={mode === 'login' ? 'selected' : ''} onClick={() => setMode('login')} type="button">
              Login
            </button>
            <button className={mode === 'register' ? 'selected' : ''} onClick={() => setMode('register')} type="button">
              Register
            </button>
          </div>

          <div className="stack">
            <label>
              Email
              <input value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>

            <label>
              Password
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </label>

            <button onClick={handleAuth} type="button">
              {mode === 'login' ? 'Login' : 'Register'}
            </button>
          </div>

          <div className="result-box">
            <strong>Status:</strong>
            <pre>{status}</pre>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="app-shell notes-shell">
      <aside className="sidebar panel">
        <div className="sidebar-header">
          <h2>Your notes</h2>
          <button className="ghost-button" onClick={handleLogout} type="button">
            Log out
          </button>
        </div>

        <button className="primary-button" onClick={() => resetForm()} type="button">
          + New note
        </button>

        <ul className="note-list">
          {notes.length === 0 ? (
            <li className="empty-state">No notes yet.</li>
          ) : (
            notes.map((note) => (
              <li key={note.id} className={selectedNoteId === note.id ? 'selected-note' : ''}>
                <button type="button" onClick={() => handleSelectNote(note)}>
                  <strong>{note.title || 'Untitled note'}</strong>
                  <small>{formatDate(note.updated_at)}</small>
                </button>
                <button className="delete-button" type="button" onClick={() => handleDeleteNote(note.id)}>
                  Delete
                </button>
              </li>
            ))
          )}
        </ul>
      </aside>

      <section className="panel editor-panel">
        <div className="editor-header">
          <h2>{selectedNoteId ? 'Edit note' : 'Create note'}</h2>
          {selectedNote && (
            <div className="note-meta">
              <span>Created: {formatDate(selectedNote.created_at)}</span>
              <span>Updated: {formatDate(selectedNote.updated_at)}</span>
            </div>
          )}
        </div>

        <div className="stack">
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>

          <label>
            Content
            <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={12} />
          </label>

          <div className="actions-row">
            <button onClick={handleSaveNote} type="button">
              {selectedNoteId ? 'Save changes' : 'Create note'}
            </button>
            {selectedNoteId && (
              <button className="secondary-button" onClick={resetForm} type="button">
                Cancel
              </button>
            )}
          </div>
        </div>

        <div className="chat-panel">
          <div className="chat-header">
            <h3>Ask your notes</h3>
          </div>

          <div className="chat-input-row">
            <textarea
              value={chatQuestion}
              onChange={(e) => setChatQuestion(e.target.value)}
              rows={3}
              placeholder="Ask a question about your notes..."
            />
            <button onClick={handleAskQuestion} type="button" disabled={chatLoading}>
              {chatLoading ? 'Thinking...' : 'Ask'}
            </button>
          </div>

          <div className="chat-output">
            {chatAnswer ? (
              <>
                <p className="chat-answer">{chatAnswer}</p>
                {chatSources.length > 0 && (
                  <ul className="source-list">
                    {chatSources.map((source) => (
                      <li key={`${source.note_id}-${source.chunk_text}`} className="source-card">
                        <strong>{source.title}</strong>
                        <span>{source.chunk_text}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p className="empty-chat">Ask about your notes and the app will answer from the relevant chunks.</p>
            )}
          </div>
        </div>

        <div className="result-box">
          <strong>Status:</strong>
          <pre>{status}</pre>
        </div>
      </section>
    </main>
  )
}

export default App
