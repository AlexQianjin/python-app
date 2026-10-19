import { clearApiToken, getApiToken } from '../../auth'
import { request } from '../../products/api/products-api'

export type AiDocument = {
  id: string
  filename: string
  size_bytes: number
  status: 'queued' | 'processing' | 'ready' | 'failed'
  error: string | null
  chunk_count: number
  created_at: string
}

export type Citation = {
  number: number
  document_id: string
  filename: string
  page: number
  chunk: number
}

export type AiMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  created_at: string
}

export type ConversationSummary = {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export type Conversation = ConversationSummary & {
  messages: AiMessage[]
}

export type Memory = { id: string; memory: string }

export const listDocuments = () => request<AiDocument[]>('/api/ai/documents')
export const retryDocument = (id: string) =>
  request<AiDocument>(`/api/ai/documents/${id}/retry`, { method: 'POST' })
export const deleteDocument = (id: string) =>
  request<void>(`/api/ai/documents/${id}`, { method: 'DELETE' })
export const listConversations = () => request<ConversationSummary[]>('/api/ai/conversations')
export const getConversation = (id: string) => request<Conversation>(`/api/ai/conversations/${id}`)
export const createConversation = () =>
  request<Conversation>('/api/ai/conversations', { method: 'POST', body: JSON.stringify({}) })
export const deleteConversation = (id: string) =>
  request<void>(`/api/ai/conversations/${id}`, { method: 'DELETE' })
export const listMemories = () => request<Memory[]>('/api/ai/memories')
export const deleteMemory = (id: string) =>
  request<void>(`/api/ai/memories/${id}`, { method: 'DELETE' })

export async function uploadDocument(file: File): Promise<AiDocument> {
  const body = new FormData()
  body.append('file', file)
  const response = await fetch('/api/ai/documents', {
    method: 'POST',
    headers: { Authorization: `Bearer ${await getApiToken()}` },
    body,
  })
  if (response.status === 401) clearApiToken()
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? `Upload failed (${response.status})`)
  }
  return response.json() as Promise<AiDocument>
}

export async function openDocument(id: string, page: number): Promise<void> {
  const tab = window.open('', '_blank')
  if (tab) tab.opener = null
  try {
    const response = await fetch(`/api/ai/documents/${id}/file`, {
      headers: { Authorization: `Bearer ${await getApiToken()}` },
    })
    if (!response.ok) throw new Error('Could not open source file')
    const url = URL.createObjectURL(await response.blob())
    if (tab) tab.location.href = `${url}#page=${page}`
    else window.location.href = `${url}#page=${page}`
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (error) {
    tab?.close()
    throw error
  }
}

export type StreamEvent =
  | { type: 'started'; conversation_id: string; message_id: string }
  | { type: 'progress'; stage: string }
  | { type: 'sources'; items: Citation[] }
  | { type: 'answer_delta'; text: string }
  | { type: 'completed'; citations: Citation[] }
  | { type: 'error'; message: string }

export async function streamMessage(
  conversationId: string,
  content: string,
  documentIds: string[],
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`/api/ai/conversations/${conversationId}/messages/stream`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${await getApiToken()}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content, document_ids: documentIds }),
    signal,
  })
  if (response.status === 401) clearApiToken()
  if (!response.ok || !response.body) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.detail ?? `Chat failed (${response.status})`)
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let completed = false
  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, '\n')
    let boundary = buffer.indexOf('\n\n')
    while (boundary >= 0) {
      const frame = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)
      const kind = frame.match(/^event: (.+)$/m)?.[1]
      const data = frame.match(/^data: (.+)$/m)?.[1]
      if (kind && data) {
        const parsed = { type: kind, ...JSON.parse(data) } as StreamEvent
        onEvent(parsed)
        if (kind === 'completed') completed = true
        if (kind === 'error') throw new Error((parsed as { message: string }).message)
      }
      boundary = buffer.indexOf('\n\n')
    }
    if (done) break
  }
  if (!completed) throw new Error('The connection closed before the response finished')
}
