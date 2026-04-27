import { useState } from 'react'

export default function Sidebar({
  siteLoaded,
  crawling,
  currentUrl,
  pageCount,
  recordCount,
  onLoadSite,
  onExport,
  hasRecords,
}) {
  const [url, setUrl] = useState('')
  const [maxPages, setMaxPages] = useState(5)
  const [useJs, setUseJs] = useState(false)
  const [fields, setFields] = useState('')
  const [exportFmt, setExportFmt] = useState('csv')

  const handleLoad = () => {
    if (!url.trim()) return
    const fieldsArray = fields.split(',').map(f => f.trim()).filter(f => f !== '')
    onLoadSite(url.trim(), maxPages, useJs, fieldsArray.length > 0 ? fieldsArray : null)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleLoad()
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-inner">
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-brand-title">
            <span></span> AI Web Scraper
          </div>
        </div>

        {/* URL Input */}
        <div className="sidebar-label">Target Website</div>
        <input
          id="url-input"
          className="input-field"
          type="url"
          placeholder="https://example.com"
          value={url}
          onChange={e => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={crawling}
        />

        {/* Required Fields */}
        <div className="sidebar-label" style={{ marginTop: 12 }}>Required Fields (Optional)</div>
        <textarea
          id="fields-input"
          className="input-field"
          style={{ height: 60, resize: 'none', fontSize: '0.8rem' }}
          placeholder="e.g. leadership names, prices, founders"
          value={fields}
          onChange={e => setFields(e.target.value)}
          disabled={crawling}
        />
        <div className="site-info" style={{ marginTop: 2, marginBottom: 8, fontSize: '0.7rem', color: '#6366f1' }}>
          💡 AI will prioritize pages matching these fields.
        </div>

        {/* Options */}
        <div className="options-row">
          <div className="option-group">
            <label className="option-label" htmlFor="max-pages-input">Max Pages</label>
            <input
              id="max-pages-input"
              type="number"
              min={1}
              max={50}
              value={maxPages}
              onChange={e => setMaxPages(Number(e.target.value))}
              className="number-input"
              disabled={crawling}
            />
          </div>
          <div className="option-group">
            <span className="option-label">JS Mode</span>
            <div className="toggle-wrap">
              <label className="toggle" htmlFor="js-toggle">
                <input
                  id="js-toggle"
                  type="checkbox"
                  checked={useJs}
                  onChange={e => setUseJs(e.target.checked)}
                  disabled={crawling}
                />
                <div className="toggle-track" />
                <div className="toggle-thumb" />
              </label>
              <span className="toggle-label-text" onClick={() => !crawling && setUseJs(v => !v)}>
                {useJs ? 'On' : 'Off'}
              </span>
            </div>
          </div>
        </div>

        <button
          id="load-site-btn"
          className="btn-primary"
          onClick={handleLoad}
          disabled={crawling || !url.trim()}
        >
          {crawling ? (
            <><div className="spin" /> Crawling…</>
          ) : (
            <>Load Site</>
          )}
        </button>

        <div className="sidebar-divider" />

        {/* Status */}
        <div className="sidebar-label">Status</div>
        {crawling ? (
          <span className="status-badge badge-loading">
            <span className="badge-dot" /> Crawling…
          </span>
        ) : siteLoaded ? (
          <>
            <span className="status-badge badge-ready">
              <span className="badge-dot" /> Site Ready
            </span>
            <div className="site-info">
              <span>{pageCount} pages cached</span>
              <span title={currentUrl}> {currentUrl.length > 34 ? currentUrl.slice(0, 34) + '…' : currentUrl}</span>
            </div>
          </>
        ) : (
          <span className="status-badge badge-idle">
            <span className="badge-dot" /> No site loaded
          </span>
        )}

        {/* Export */}
        {hasRecords && (
          <>
            <div className="sidebar-divider" />
            <div className="sidebar-label">Export Results</div>
            <select
              id="export-format-select"
              className="export-select"
              value={exportFmt}
              onChange={e => setExportFmt(e.target.value)}
            >
              <option value="csv">CSV</option>
              <option value="json">JSON</option>
              <option value="excel">Excel (.xlsx)</option>
            </select>
            <button
              id="export-btn"
              className="btn-export"
              onClick={() => onExport(exportFmt)}
            >
              <span></span> Download {exportFmt.toUpperCase()}
            </button>
            <div className="site-info" style={{ marginTop: 6 }}>
              <span>{recordCount} records available</span>
            </div>
          </>
        )}
      </div>
    </aside>
  )
}
