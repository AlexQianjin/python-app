import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  createConversation,
  deleteConversation,
  deleteDocument,
  deleteMemory,
  getConversation,
  listConversations,
  listDocuments,
  listMemories,
  openDocument,
  retryDocument,
  streamMessage,
  uploadDocument,
  type AiMessage,
  type Citation,
} from '../api/ai-api'

export function AiPage() {
  const queryClient = useQueryClient()
  const conversations = useQuery({ queryKey: ['ai-conversations'], queryFn: listConversations })
  const documents = useQuery({
    queryKey: ['ai-documents'],
    queryFn: listDocuments,
    refetchInterval: 3000,
  })
  const memories = useQuery({
    queryKey: ['ai-memories'],
    queryFn: listMemories,
    refetchInterval: 5000,
  })
  const [conversationId, setConversationId] = useState<string | null>(null)
  const conversation = useQuery({
    queryKey: ['ai-conversation', conversationId],
    queryFn: () => getConversation(conversationId!),
    enabled: Boolean(conversationId),
  })
  const [selected, setSelected] = useState<string[]>([])
  const [draft, setDraft] = useState('')
  const [pendingQuestion, setPendingQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<Citation[]>([])
  const [error, setError] = useState('')
  const abort = useRef<AbortController | null>(null)
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth' })
  }, [answer, conversation.data?.messages.length])

  useEffect(() => () => abort.current?.abort(), [])

  async function perform(action: () => Promise<void>) {
    try {
      setError('')
      await action()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Action failed')
    }
  }

  async function onUpload(files: FileList | null) {
    if (!files?.length) return
    setUploading(true)
    setError('')
    try {
      for (const file of Array.from(files)) await uploadDocument(file)
      await queryClient.invalidateQueries({ queryKey: ['ai-documents'] })
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  async function send() {
    const content = draft.trim()
    if (!content || busy) return
    setBusy(true)
    setDraft('')
    setPendingQuestion(content)
    setAnswer('')
    setSources([])
    setProgress('Starting…')
    setError('')
    let activeId = conversationId
    try {
      if (!activeId) {
        const created = await createConversation()
        activeId = created.id
        setConversationId(activeId)
        await queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
      }
      const controller = new AbortController()
      abort.current = controller
      await streamMessage(
        activeId,
        content,
        selected,
        (item) => {
          if (item.type === 'started') setProgress('Searching documents…')
          if (item.type === 'progress') setProgress('Trying another search…')
          if (item.type === 'sources') setSources(item.items)
          if (item.type === 'answer_delta') {
            setProgress('Writing answer…')
            setAnswer((current) => current + item.text)
          }
          if (item.type === 'completed') setSources(item.citations)
        },
        controller.signal,
      )
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['ai-conversation', activeId] }),
        queryClient.invalidateQueries({ queryKey: ['ai-conversations'] }),
        queryClient.invalidateQueries({ queryKey: ['ai-memories'] }),
      ])
      setAnswer('')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Chat failed')
      setDraft(content)
    } finally {
      if (activeId) {
        await queryClient.invalidateQueries({ queryKey: ['ai-conversation', activeId] })
      }
      setPendingQuestion('')
      setBusy(false)
      setProgress('')
      abort.current = null
    }
  }

  function toggleDocument(id: string) {
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    )
  }

  const messageList: AiMessage[] = conversation.data?.messages ?? []

  return (
    <main className="page-content ai-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Knowledge assistant</p>
          <h1>AI Chat</h1>
          <p className="intro">Ask questions about your files and follow the sources.</p>
        </div>
        <button
          className="button secondary"
          type="button"
          onClick={() => {
            setConversationId(null)
            setAnswer('')
            setError('')
          }}
        >
          New chat
        </button>
      </header>
      {error && (
        <div className="commerce-error" role="alert">
          {error}
        </div>
      )}
      <div className="ai-grid">
        <aside className="ai-panel">
          <h2>Conversations</h2>
          <div className="ai-list">
            {conversations.data?.map((item) => (
              <div className="ai-list-row" key={item.id}>
                <button
                  className={conversationId === item.id ? 'selected' : ''}
                  type="button"
                  onClick={() => {
                    setConversationId(item.id)
                    setAnswer('')
                  }}
                >
                  {item.title}
                </button>
                <button
                  type="button"
                  aria-label={`Delete ${item.title}`}
                  onClick={() =>
                    void perform(async () => {
                      await deleteConversation(item.id)
                      if (conversationId === item.id) setConversationId(null)
                      await queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
                    })
                  }
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          <h2>Your files</h2>
          <label className="button secondary ai-upload">
            {uploading ? 'Uploading…' : 'Upload files'}
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md"
              disabled={uploading}
              onChange={(event) => {
                void onUpload(event.target.files)
                event.target.value = ''
              }}
            />
          </label>
          <p className="ai-hint">PDF, DOCX, TXT or Markdown · up to 20 MB each</p>
          <div className="ai-list">
            {documents.data?.map((item) => (
              <div className="ai-file" key={item.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={selected.includes(item.id)}
                    disabled={item.status !== 'ready'}
                    onChange={() => toggleDocument(item.id)}
                  />{' '}
                  <span>{item.filename}</span>
                </label>
                <small>
                  {item.status}
                  {item.error ? ` · ${item.error}` : ''}
                </small>
                <div className="ai-file-actions">
                  {item.status === 'failed' && (
                    <button
                      type="button"
                      onClick={() =>
                        void perform(async () => {
                          await retryDocument(item.id)
                          await queryClient.invalidateQueries({ queryKey: ['ai-documents'] })
                        })
                      }
                    >
                      Retry
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() =>
                      void perform(async () => {
                        await deleteDocument(item.id)
                        setSelected((current) => current.filter((id) => id !== item.id))
                        await queryClient.invalidateQueries({ queryKey: ['ai-documents'] })
                      })
                    }
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
          <details className="ai-memory">
            <summary>Saved memories</summary>
            {memories.data?.length ? (
              memories.data.map((item) => (
                <div className="ai-list-row" key={item.id}>
                  <span>{item.memory}</span>
                  <button
                    type="button"
                    onClick={() =>
                      void perform(async () => {
                        await deleteMemory(item.id)
                        await queryClient.invalidateQueries({ queryKey: ['ai-memories'] })
                      })
                    }
                  >
                    ×
                  </button>
                </div>
              ))
            ) : (
              <p>No memories saved.</p>
            )}
          </details>
        </aside>
        <section className="ai-chat" aria-label="Conversation">
          <div className="ai-messages">
            {!messageList.length && !busy && (
              <div className="ai-empty">
                <h2>Start a conversation</h2>
                <p>Select ready files, then ask a question. You can also chat without files.</p>
              </div>
            )}
            {messageList.map((item) => (
              <article className={`ai-message ${item.role}`} key={item.id}>
                <strong>{item.role === 'user' ? 'You' : 'Assistant'}</strong>
                <p>{item.content}</p>
                {!!item.citations.length && (
                  <div className="ai-citations">
                    {item.citations.map((cite) => (
                      <button
                        key={`${item.id}-${cite.number}`}
                        type="button"
                        onClick={() =>
                          void perform(() => openDocument(cite.document_id, cite.page))
                        }
                      >
                        [{cite.number}] {cite.filename}, p. {cite.page}
                      </button>
                    ))}
                  </div>
                )}
              </article>
            ))}
            {busy && pendingQuestion && (
              <article className="ai-message user">
                <strong>You</strong>
                <p>{pendingQuestion}</p>
              </article>
            )}
            {busy && (
              <article className="ai-message assistant">
                <strong>Assistant</strong>
                <small>{progress}</small>
                <p>{answer || 'Working…'}</p>
                {!!sources.length && <small>{sources.length} source chunks found</small>}
              </article>
            )}
            <div ref={bottom} />
          </div>
          <form
            className="ai-compose"
            onSubmit={(event) => {
              event.preventDefault()
              void send()
            }}
          >
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  void send()
                }
              }}
              placeholder="Ask a question…"
              rows={3}
              aria-label="Message"
            />
            <div>
              <span>
                {selected.length
                  ? `${selected.length} file${selected.length === 1 ? '' : 's'} selected`
                  : 'No files selected'}
              </span>
              {busy ? (
                <button
                  className="button secondary"
                  type="button"
                  onClick={() => abort.current?.abort()}
                >
                  Stop
                </button>
              ) : (
                <button className="button primary" type="submit" disabled={!draft.trim()}>
                  Send
                </button>
              )}
            </div>
          </form>
        </section>
      </div>
    </main>
  )
}
