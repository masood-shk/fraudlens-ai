import { useEffect, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'https://fraudlens-ai-2vyx.onrender.com'

function App() {
  const [file, setFile] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('fraudlens-history') || '[]')
    } catch {
      return []
    }
  })

  useEffect(() => {
    localStorage.setItem('fraudlens-history', JSON.stringify(history))
  }, [history])

  const handleFileChange = (e) => {
    setError(null)
    setResult(null)
    if (e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setError(null)
    setResult(null)
    if (e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleAnalyze = async () => {
    if (!file) {
      setError('Please upload a file first.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_URL}/api/analyze`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || `Failed to analyze the invoice (${response.status}).`)
      }
      const fraud = data.fraud_analysis || {}
      const invoice = data.extracted_invoice || {}
      const vendorMatch = data.vendor_match || {}
      const ruleSignals = fraud.rule_based_analysis?.signals || []

      const normalizedResult = {
        decision: (fraud.decision || 'REVIEW').toLowerCase(),
        score: Number(fraud.final_risk_score || 0),
        reason: fraud.reason || ruleSignals[0]?.message || 'Analysis completed.',
        invoice_amount: Number(invoice.total_amount || 0),
        vendor: vendorMatch.vendor_name || invoice.vendor_name || 'Unknown',
        invoice_date: invoice.invoice_date || 'N/A',
        invoice_number: invoice.invoice_number || 'N/A',
        purchase_order: invoice.po_id || 'N/A',
        payment_terms: invoice.payment_terms || 'N/A',
        signals: ruleSignals.map((signal, index) => ({
          id: `${signal.check || 'signal'}-${index}`,
          severity: signal.severity || 'medium',
          title: (signal.check || 'Fraud signal').replaceAll('_', ' '),
          description: signal.message || 'Potential fraud signal detected.',
        })),
      }
      setResult(normalizedResult)
      setHistory((currentHistory) => [
        {
          id: `${Date.now()}-${normalizedResult.invoice_number}`,
          invoice_number: normalizedResult.invoice_number,
          vendor: normalizedResult.vendor,
          invoice_date: normalizedResult.invoice_date,
          invoice_amount: normalizedResult.invoice_amount,
          score: normalizedResult.score,
          decision: normalizedResult.decision,
          analyzed_at: new Date().toISOString(),
        },
        ...currentHistory,
      ].slice(0, 10))
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="brand">
          <div className="brand-mark">FL</div>
          <div className="brand-copy">
            <strong className="brand-name">FraudLens AI</strong>
            <span className="brand-tagline">Invoice Fraud Intelligence</span>
          </div>
        </div>
        <div className="system-status">
          <div className="status-dot"></div> System Online
        </div>
      </nav>

      <header className="hero-section">
        <p className="eyebrow">Invoice Fraud Detection</p>
        <h1>
          Analyze <span>Invoices</span> with AI
        </h1>
        <p>
          Upload your invoice in PDF, PNG, JPG, or JPEG format to detect potential fraud risks and review detailed fraud signals.
        </p>
      </header>

      <main className="workspace">
        <section className="upload-card panel">
          <div className="panel-heading">
            <h2>Upload Invoice</h2>
          </div>
          <div
            className={`drop-zone${file ? ' has-file' : ''}`}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            onClick={() => document.getElementById('file-input').click()}
          >
            <div className="upload-icon">📄</div>
            {file ? (
              <strong>{file.name}</strong>
            ) : (
              <>
                <strong>Drag & drop your invoice here</strong>
                <span>or click to select a file</span>
                <span>PDF, PNG, JPG, or JPEG</span>
              </>
            )}
            <input
              id="file-input"
              type="file"
              accept="application/pdf,image/png,image/jpeg,.pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
            />
          </div>

          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={loading || !file}
          >
            {loading ? 'Analyzing...' : 'Analyze Invoice'}
          </button>

          {error && <div className="error-message">{error}</div>}
        </section>

        <section className="result-card panel">
          <div className="panel-heading">
            <h2>Risk Assessment</h2>
          </div>
          {!result && !loading && (
            <div className="empty-state">
              <div className="scan-ring">🔍</div>
              <strong>No analysis yet</strong>
              <span>Upload an invoice to get started</span>
            </div>
          )}

          {loading && (
            <div className="empty-state">
              <div className="loader"></div>
              <span>Analyzing invoice...</span>
            </div>
          )}

          {result && (
            <>
              <div className="decision-content">
                <div
                  className={`decision-badge ${
                    result.decision === 'block'
                      ? 'block'
                      : result.decision === 'review'
                      ? 'review'
                      : 'approve'
                  }`}
                >
                  {result.decision.toUpperCase()}
                </div>
                <div className="score-row">
                  <div>
                    <span>Fraud Risk Score</span>
                    <strong>{result.score.toFixed(1)}</strong>
                  </div>
                  <small>0 (low) - 100 (high)</small>
                  <div className="score-bar">
                    <div style={{ width: `${result.score}%` }}></div>
                  </div>
                </div>
                <div className="decision-reason">{result.reason}</div>
              </div>

              <div className="quick-stats">
                <div>
                  <span>Invoice Amount</span>
                  <strong>${result.invoice_amount.toFixed(2)}</strong>
                </div>
                <div>
                  <span>Vendor</span>
                  <strong>{result.vendor}</strong>
                </div>
                <div>
                  <span>Date</span>
                  <strong>{result.invoice_date}</strong>
                </div>
              </div>

              <div className="detail-panel">
                <h3>Invoice Details</h3>
                <div className="detail-list">
                  <div>
                    <span>Invoice Number:</span>
                    <strong>{result.invoice_number}</strong>
                  </div>
                  <div>
                    <span>Purchase Order:</span>
                    <strong>{result.purchase_order || 'N/A'}</strong>
                  </div>
                  <div>
                    <span>Payment Terms:</span>
                    <strong>{result.payment_terms || 'N/A'}</strong>
                  </div>
                </div>

                <h3>Fraud Signals</h3>
                {result.signals.length === 0 && (
                  <div className="clean-signal">No fraud signals detected.</div>
                )}
                <div className="signals-list">
                  {result.signals.map(({ id, severity, title, description }) => (
                    <div key={id} className="signal">
                      <div className={`severity ${severity.toLowerCase()}`}>
                        {severity}
                      </div>
                      <div>
                        <strong>{title}</strong>
                        <p>{description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </section>

        <section className="history-card panel">
          <div className="history-heading">
            <div>
              <p className="history-eyebrow">Recent Activity</p>
              <h2>Analysis History</h2>
            </div>
            <div className="history-actions">
              <span>{history.length} {history.length === 1 ? 'analysis' : 'analyses'}</span>
              {history.length > 0 && (
                <button
                  type="button"
                  className="clear-history-button"
                  onClick={() => setHistory([])}
                >
                  Clear History
                </button>
              )}
            </div>
          </div>

          {history.length === 0 ? (
            <div className="history-empty">
              <strong>No analysis history yet</strong>
              <span>Completed invoice analyses will appear here.</span>
            </div>
          ) : (
            <div className="history-table-wrap">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Invoice</th>
                    <th>Vendor</th>
                    <th>Amount</th>
                    <th>Risk Score</th>
                    <th>Decision</th>
                    <th>Analyzed</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((item) => (
                    <tr key={item.id}>
                      <td>{item.invoice_number}</td>
                      <td>{item.vendor}</td>
                      <td>${Number(item.invoice_amount).toFixed(2)}</td>
                      <td>
                        <div className="history-risk">
                          <span>{Number(item.score).toFixed(1)}</span>
                          <div className="history-risk-track">
                            <div style={{ width: `${Math.min(Number(item.score), 100)}%` }} />
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className={`history-decision ${item.decision}`}>
                          {item.decision.toUpperCase()}
                        </span>
                      </td>
                      <td>{new Date(item.analyzed_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
