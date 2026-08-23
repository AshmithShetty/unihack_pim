import { useState, useRef, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Send, Bot, User, Code2, ChevronDown, ChevronRight, Loader2, Database } from 'lucide-react'
import axios from '../api/axios'
import clsx from 'clsx'

export default function Chatbot() {
  const { id } = useParams()
  const [messages, setMessages] = useState([
    { id: '1', role: 'assistant', text: `Hello! I am Vanna AI, your data assistant for Project #${id}. You can ask me questions specifically about this project's output data.` }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (e) => {
    e?.preventDefault()
    if (!input.trim() || loading) return

    const userMsg = input.trim()
    setInput('')
    
    // Add user message
    const msgId = Date.now().toString()
    setMessages(prev => [...prev, { id: msgId, role: 'user', text: userMsg }])
    
    setLoading(true)

    try {
      const res = await axios.post('/api/chat', { question: userMsg, project_id: parseInt(id) })
      
      setMessages(prev => [...prev, { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        text: res.data.answer || 'Here are the results.',
        sql: res.data.sql,
        results: res.data.results
      }])
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, { 
        id: (Date.now() + 1).toString(), 
        role: 'assistant', 
        text: 'Sorry, I encountered an error executing that query. Please try rephrasing.',
        error: true
      }])
    } finally {
      setLoading(false)
    }
  }

  const SqlBlock = ({ sql }) => {
    const [expanded, setExpanded] = useState(false)
    if (!sql) return null

    return (
      <div className="mt-3 border border-slate-200 rounded-lg overflow-hidden bg-slate-50">
        <button 
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
        >
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          <Code2 size={14} />
          View generated SQL
        </button>
        {expanded && (
          <div className="p-3 bg-[#1e1e1e] text-[#d4d4d4] text-xs font-mono overflow-x-auto whitespace-pre-wrap">
            {sql}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-120px)] flex flex-col bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg text-white">
            <Database size={20} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 leading-tight">Data Chatbot</h1>
            <p className="text-xs text-slate-500">Powered by Vanna AI</p>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className={clsx("flex gap-4 max-w-[85%]", msg.role === 'user' ? "ml-auto flex-row-reverse" : "")}>
            <div className={clsx(
              "w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1",
              msg.role === 'user' ? "bg-slate-800 text-white" : "bg-blue-100 text-blue-600"
            )}>
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            
            <div className={clsx(
              "p-4 rounded-2xl",
              msg.role === 'user' ? "bg-slate-800 text-white rounded-tr-sm" : 
              msg.error ? "bg-red-50 text-red-700 border border-red-200 rounded-tl-sm" :
              "bg-slate-50 border border-slate-200 text-slate-900 rounded-tl-sm"
            )}>
              <div className="text-sm whitespace-pre-wrap">{msg.text}</div>
              
              {msg.sql && <SqlBlock sql={msg.sql} />}
              
              {msg.results && msg.results.length > 0 && (
                <div className="mt-3 text-xs text-slate-500 bg-white border border-slate-200 p-2 rounded-lg">
                  <span className="font-semibold">{msg.results.length}</span> rows returned.
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-4 max-w-[85%]">
            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center shrink-0 mt-1">
              <Bot size={16} />
            </div>
            <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-slate-500 rounded-tl-sm flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-200">
        <form onSubmit={handleSend} className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question in plain English..."
            className="w-full pl-4 pr-12 py-3 border border-slate-300 rounded-xl focus:border-blue-500 focus:ring-blue-500 shadow-sm text-sm"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  )
}
