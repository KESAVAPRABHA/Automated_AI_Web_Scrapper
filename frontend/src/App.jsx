import { useState, useRef, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'
import './index.css'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [messages, setMessages] = useState([])
  const [crawledPages, setCrawledPages] = useState([])
  const [currentUrl, setCurrentUrl] = useState('')
  const [siteLoaded, setSiteLoaded] = useState(false)
  const [crawling, setCrawling] = useState(false)
  const [thinking, setThinking] = useState(false)
  const [lastRecords, setLastRecords] = useState([])

  const addMessage = useCallback((role, content, data = []) => {
    setMessages(prev => [...prev, { role, content, data, id: Date.now() + Math.random() }])
  }, [])

  const handleLoadSite = useCallback(async (url, maxPages, useJs) => {
    setCrawling(true)
    setMessages([])
    setLastRecords([])
    setSiteLoaded(false)
    try {
      const res = await fetch(`${API_BASE}/api/crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, max_pages: maxPages, use_js: useJs }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Crawl failed')
      }
      const data = await res.json()
      setCrawledPages(data.pages)
      setCurrentUrl(url)
      setSiteLoaded(true)
      addMessage('assistant',
        `<b>Site loaded!</b> I crawled <b>${data.count}</b> page(s) from <code>${url}</code>.<br><br>` +
        `Now ask me anything — for example:<br>` +
        `• <i>"Give me the leadership team names"</i><br>` +
        `• <i>"What products do they sell and at what price?"</i><br>` +
        `• <i>"Are there any frontend engineering openings?"</i>`,
        []
      )
    } catch (err) {
      addMessage('assistant', `⚠️ <b>Crawl failed:</b> ${err.message}`)
    } finally {
      setCrawling(false)
    }
  }, [addMessage])

  const handleChat = useCallback(async (userQuery) => {
    if (!userQuery.trim() || !siteLoaded) return
    addMessage('user', userQuery)
    setThinking(true)
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_query: userQuery,
          pages: crawledPages,
          url: currentUrl,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'AI error')
      }
      const data = await res.json()
      if (data.data && data.data.length > 0) {
        setLastRecords(data.data)
      }
      addMessage('assistant', data.answer || 'Here\'s what I found:', data.data || [])
    } catch (err) {
      addMessage('assistant', `⚠️ <b>Error:</b> ${err.message}<br><br>Make sure the FastAPI backend is running on port 8000.`)
    } finally {
      setThinking(false)
    }
  }, [siteLoaded, crawledPages, currentUrl, addMessage])

  const handleExport = useCallback(async (fmt) => {
    if (!lastRecords.length) return
    try {
      const res = await fetch(`${API_BASE}/api/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ records: lastRecords, fmt }),
      })
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const extMap = { csv: 'csv', json: 'json', excel: 'xlsx' }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scraper_results.${extMap[fmt] || fmt}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert('Export failed: ' + err.message)
    }
  }, [lastRecords])

  return (
    <div className="app-layout">
      <Sidebar
        siteLoaded={siteLoaded}
        crawling={crawling}
        currentUrl={currentUrl}
        pageCount={crawledPages.length}
        recordCount={lastRecords.length}
        onLoadSite={handleLoadSite}
        onExport={handleExport}
        hasRecords={lastRecords.length > 0}
      />
      <main className="main-area">
        <header className="hero-header">
          <div className="hero-glow" />
          <div className="hero-content">
            <span className="hero-icon">🕸️</span>
            <div>
              <h1 className="hero-title">AI Web Scraper</h1>
            </div>
          </div>
        </header>

        {siteLoaded && (
          <div className="stats-row">
            <div className="stat-card">
              <span className="stat-value">{crawledPages.length}</span>
              <span className="stat-label">Pages Crawled</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{messages.length}</span>
              <span className="stat-label">Messages</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{lastRecords.length}</span>
              <span className="stat-label">Records Extracted</span>
            </div>
          </div>
        )}

        <ChatWindow messages={messages} thinking={thinking} siteLoaded={siteLoaded} />
        <ChatInput onSend={handleChat} disabled={!siteLoaded || thinking} thinking={thinking} />
      </main>
    </div>
  )
}
