import { useState, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || ''

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const sendMessage = useCallback(async (question) => {
    // Add user message
    const userMessage = { role: 'user', content: question }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || `Server error (${response.status})`)
      }

      const data = await response.json()

      // Add assistant message
      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        context_used: data.context_used,
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
      // Add error message to chat
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.', isError: true },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return { messages, isLoading, error, sendMessage, clearChat }
}
