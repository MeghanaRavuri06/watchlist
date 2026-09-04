import { useEffect, useState } from 'react'
import { api } from './api.js'

const FLAG_LABELS = {
  volatility: 'Unusual move',
  volume_spike: 'Volume spike',
  target_hit: 'Target hit',
  data_unavailable: 'Data unavailable',
}

function AddForm({ onAdded }) {
  const [symbol, setSymbol] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [reason, setReason] = useState('')
  const [targetPrice, setTargetPrice] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!symbol.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      await api.addItem({
        symbol: symbol.trim(),
        display_name: displayName.trim() || null,
        reason: reason.trim() || null,
        target_price: targetPrice ? parseFloat(targetPrice) : null,
      })
      setSymbol('')
      setDisplayName('')
      setReason('')
      setTargetPrice('')
      onAdded()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="add-form" onSubmit={handleSubmit}>
      <div className="row">
        <div>
          <label htmlFor="symbol">Symbol (e.g. RELIANCE.NS)</label>
          <input
            id="symbol"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="TCS.NS"
            required
          />
        </div>
        <div>
          <label htmlFor="displayName">Display name (optional)</label>
          <input
            id="displayName"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Tata Consultancy Services"
          />
        </div>
      </div>
      <div>
        <label htmlFor="reason">Why are you watching this?</label>
        <textarea
          id="reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Watching before Q2 earnings, want in if it breaks 4200"
        />
      </div>
      <div className="row">
        <div>
          <label htmlFor="target">Target price (optional)</label>
          <input
            id="target"
            type="number"
            step="0.01"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            placeholder="4200"
          />
        </div>
      </div>
      {error && <div className="error-state">{error}</div>}
      <button type="submit" disabled={submitting}>
        {submitting ? 'Adding…' : 'Add to watchlist'}
      </button>
    </form>
  )
}

function WatchlistView({ items, loading, error, onDelete }) {
  const [expanded, setExpanded] = useState({})

  const toggleDetails = (id) => {
    setExpanded((current) => ({ ...current, [id]: !current[id] }))
  }
  if (loading) return <div className="loading">Loading prices…</div>
  if (error) return <div className="error-state">{error}</div>
  if (items.length === 0) {
    return (
      <div className="empty-state">
        Nothing on your watchlist yet — add a stock above to start tracking it.
      </div>
    )
  }

  return (
    <div className="watchlist">
      <div className="table-head">
        <div>Symbol</div>
        <div className="num">Price</div>
        <div className="num">Flags</div>
        <div></div>
      </div>
      {items.map((item) => {
        const hasDetails = item.z_score != null || item.volume_ratio != null
        return (
          <div className="item-card" key={item.id}>
            <div className="row-item">
              <div className="symbol-block">
                <div className="symbol">{item.symbol}</div>
                {item.display_name && <div className="name">{item.display_name}</div>}
                {item.reason && <div className="reason">{item.reason}</div>}
              </div>

              <div className="price-block">
                {item.price != null ? (
                  <>
                    <div className="price">₹{item.price.toFixed(2)}</div>
                    <div className={`change ${item.pct_change >= 0 ? 'gain' : 'loss'}`}>
                      {item.pct_change >= 0 ? '+' : ''}
                      {item.pct_change}%
                    </div>
                  </>
                ) : (
                  <div className="change">—</div>
                )}
              </div>

              <div className="flags">
                {item.flags.length > 0 ? item.flags.map((flag) => (
                  <span className="flag-pill" key={flag}>
                    {FLAG_LABELS[flag] || flag}
                  </span>
                )) : <span className="no-flag">No unusual change</span>}
              </div>

              <button className="remove-btn" onClick={() => onDelete(item.id)} aria-label={`Remove ${item.symbol}`}>
                Remove
              </button>
            </div>

            <div className="row-meta">
              {item.captured_at && (
                <span className="captured-at">
                  As of {new Date(item.captured_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              {hasDetails && (
                <button className="details-btn" onClick={() => toggleDetails(item.id)}>
                  {expanded[item.id] ? 'Hide details' : 'Why?'}
                </button>
              )}
              {expanded[item.id] && (
                <div className="metric-details">
                  {item.z_score != null && <span>Z-score {item.z_score.toFixed(2)}</span>}
                  {item.volume_ratio != null && <span>Volume {item.volume_ratio.toFixed(2)}× avg</span>}
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function DiffView({ diff, loading, error }) {
  if (loading) return <div className="loading">Comparing against your last visit…</div>
  if (error) return <div className="error-state">{error}</div>
  if (!diff || diff.comparisons.length === 0) {
    return (
      <div className="empty-state">
        No comparison yet — visit the watchlist tab first so there's a snapshot
        to compare against next time you check in.
      </div>
    )
  }

  const lastVisitText = diff.last_visit_at
    ? new Date(diff.last_visit_at).toLocaleString()
    : 'your first visit'

  return (
    <div>
      <div className="diff-meta">Since {lastVisitText}</div>
      {diff.comparisons.map((c) => (
        <div
          className={`diff-row ${c.is_meaningful ? 'meaningful' : ''}`}
          key={c.symbol}
        >
          <div>
            <div className="symbol-block">
              <div className="symbol">{c.symbol}</div>
              {c.display_name && <div className="name">{c.display_name}</div>}
            </div>
            <div className="diff-tags">
              {c.target_hit && <span className="tag-target">Target hit</span>}
              {c.flags
                .filter((f) => f !== 'target_hit')
                .map((f) => (
                  <span className="flag-pill" key={f}>
                    {FLAG_LABELS[f] || f}
                  </span>
                ))}
            </div>
          </div>
          <div className="diff-compare">
            <span className="then">₹{c.price_then.toFixed(2)}</span>
            <span className="arrow">→</span>
            <span className={`now ${c.delta_pct >= 0 ? 'gain' : 'loss'}`}>
              ₹{c.price_now.toFixed(2)}
            </span>
            <span className={`change ${c.delta_pct >= 0 ? 'gain' : 'loss'}`}>
              ({c.delta_pct >= 0 ? '+' : ''}
              {c.delta_pct}%)
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState('watchlist')
  const [items, setItems] = useState([])
  const [diff, setDiff] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function loadWatchlist() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getWatchlist()
      setItems(data)
    } catch (err) {
      setError(
        `Couldn't reach the backend at http://127.0.0.1:8000 — is it running? (${err.message})`
      )
    } finally {
      setLoading(false)
    }
  }

  async function loadDiff() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getDiff()
      setDiff(data)
    } catch (err) {
      setError(`Couldn't load comparison. (${err.message})`)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWatchlist()
  }, [])

  useEffect(() => {
    if (tab === 'diff') loadDiff()
    if (tab === 'watchlist') loadWatchlist()
  }, [tab])

  async function handleDelete(id) {
    await api.deleteItem(id)
    loadWatchlist()
  }

  return (
    <div className="page">
      <header className="top">
        <h1>Catchup</h1>
      </header>
      <p className="subtitle">Track what matters, skip the noise.</p>

      <nav className="tabs">
        <button
          className={tab === 'watchlist' ? 'active' : ''}
          onClick={() => setTab('watchlist')}
        >
          Watchlist
        </button>
        <button
          className={tab === 'diff' ? 'active' : ''}
          onClick={() => setTab('diff')}
        >
          Since you last checked
        </button>
      </nav>

      {tab === 'watchlist' && (
        <>
          <AddForm onAdded={loadWatchlist} />
          <WatchlistView
            items={items}
            loading={loading}
            error={error}
            onDelete={handleDelete}
          />
        </>
      )}

      {tab === 'diff' && (
        <DiffView diff={diff} loading={loading} error={error} />
      )}
    </div>
  )
}
