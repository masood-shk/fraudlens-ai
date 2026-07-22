import { downloadInvestigationReport } from "./utils/pdfReport";
import { useEffect, useState } from 'react'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

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
      console.log("API Response:", data);

      if (!response.ok) {
        throw new Error(data.detail || `Failed to analyze the invoice (${response.status}).`)
      }
      const fraud = data.fraud_analysis || {}
      const invoice = data.extracted_invoice || {}
      const vendorMatch = data.vendor_match || {}
      const investigationReport = data.investigation_report || {}
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
        investigation_report: investigationReport,
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

  const riskDistribution = [
    { name: 'Approved', value: history.filter(item => item.decision === 'approve').length },
    { name: 'Review', value: history.filter(item => item.decision === 'review').length },
    { name: 'Blocked', value: history.filter(item => item.decision === 'block').length },
  ]

  const COLORS = ['#22c55e', '#facc15', '#ef4444']

  const trendData = history
    .slice()
    .reverse()
    .map((item, index) => ({
      analysis: index + 1,
      risk: Number(item.score),
    }))

  const averageRisk = history.length
    ? (history.reduce((sum, item) => sum + Number(item.score), 0) / history.length).toFixed(1)
    : '0.0'

  const approvalRate = history.length
    ? ((history.filter(item => item.decision === 'approve').length / history.length) * 100).toFixed(0)
    : '0'

  const highestRisk = history.reduce(
    (max, item) => (Number(item.score) > Number(max.score || -1) ? item : max),
    {}
  )
  const highRiskAlerts = history
    .filter(item => Number(item.score) >= 70)
    .sort((a, b) => Number(b.score) - Number(a.score))
    .slice(0, 5)

  const topVendors = Object.values(
    history.reduce((acc, item) => {
      if (!acc[item.vendor]) {
        acc[item.vendor] = {
          vendor: item.vendor,
          count: 0,
        }
      }

      acc[item.vendor].count += 1
      return acc
    }, {})
  )
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)

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
        <section className="analytics-summary panel">
          <div className="quick-stats">
            <div>
              <span>Total Analyses</span>
              <strong>{history.length}</strong>
            </div>
            <div>
              <span>Approved</span>
              <strong>{history.filter(item => item.decision === 'approve').length}</strong>
            </div>
            <div>
              <span>Review</span>
              <strong>{history.filter(item => item.decision === 'review').length}</strong>
            </div>
            <div>
              <span>Blocked</span>
              <strong>{history.filter(item => item.decision === 'block').length}</strong>
            </div>
            <div>
              <span>Average Risk</span>
              <strong>
                {history.length
                  ? (history.reduce((sum, item) => sum + Number(item.score), 0) / history.length).toFixed(1)
                  : '0.0'}
              </strong>
            </div>
          </div>
        </section>
        <section className="panel top-vendors">
          <div className="panel-heading">
            <div>
              <h2>Top Vendors</h2>
              <p>Most frequently analyzed vendors</p>
            </div>
          </div>

          {topVendors.length === 0 ? (
            <div className="alerts-empty">
              No vendor analytics available.
            </div>
          ) : (
            <div className="vendors-list">
              {topVendors.map((vendor, index) => (
                <div className="vendor-row" key={vendor.vendor}>
                  <div className="vendor-info">
                    <strong>{vendor.vendor}</strong>
                    <span>{vendor.count} invoice{vendor.count > 1 ? 's' : ''}</span>
                  </div>

                  <div className="vendor-progress">
                    <div
                      className="vendor-progress-fill"
                      style={{ width: `${(vendor.count / topVendors[0].count) * 100}%` }}
                    />
                  </div>

                  <strong className="vendor-rank">#{index + 1}</strong>
                </div>
              ))}
            </div>
          )}
        </section>
        <section className="panel analytics-chart">
          <div className="analytics-header">
            <div>
              <h2>Risk Distribution</h2>
              <p>Breakdown of analyses by fraud decision</p>
            </div>
          </div>

          <div className="analytics-content">
            <div className="chart-area">
              <ResponsiveContainer width="100%" height={360}>
                <PieChart>
                  <Pie
                    data={riskDistribution}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={80}
                    outerRadius={120}
                    paddingAngle={4}
                    stroke="#10151f"
                    strokeWidth={4}
                    label={false}
                    labelLine={false}
                  >
                    {riskDistribution.map((entry, index) => (
                      <Cell key={entry.name} fill={COLORS[index]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>

              <div className="chart-center">
                <span>Total</span>
                <strong>{history.length}</strong>
              </div>
            </div>

            <div className="chart-legend">
              {riskDistribution.map((item, index) => {
                const descriptions = [
                  'Automatically approved',
                  'Requires manual review',
                  'Potential fraud detected',
                ]

                const percentage = history.length
                  ? ((item.value / history.length) * 100).toFixed(1)
                  : '0.0'

                return (
                  <div className="legend-item" key={item.name}>
                    <div className="legend-left">
                      <span
                        className="legend-dot"
                        style={{ backgroundColor: COLORS[index] }}
                      />
                      <div>
                        <strong>{item.name}</strong>
                        <small>{descriptions[index]}</small>
                      </div>
                    </div>

                    <div className="legend-right">
                      <strong>{item.value}</strong>
                      <span>{percentage}%</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>
        <section className="panel trend-chart">
          <div className="panel-heading">
            <div>
              <h2>Risk Trend</h2>
              <p>Fraud risk across recent analyses</p>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid stroke="#242b36" strokeDasharray="4 4" />
              <XAxis dataKey="analysis" stroke="#7f8998" />
              <YAxis stroke="#7f8998" />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="risk"
                stroke="#4f8cff"
                strokeWidth={3}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </section>

        <section className="panel ai-insights">
          <div className="panel-heading">
            <div>
              <h2>AI Insights</h2>
              <p>Automatically generated from recent analyses</p>
            </div>
          </div>

          <div className="insight-grid">
            <div className="insight-card">
              <span>Approval Rate</span>
              <strong>{approvalRate}%</strong>
            </div>

            <div className="insight-card">
              <span>Average Risk</span>
              <strong>{averageRisk}</strong>
            </div>

            <div className="insight-card full-width">
              <span>Highest Risk Invoice</span>
              <strong>{highestRisk.invoice_number || 'N/A'}</strong>
              <small>
                {highestRisk.vendor || 'No data'} • Risk {highestRisk.score ?? '-'}
              </small>
            </div>

            <div className="insight-recommendation full-width">
              <h3>Recommendation</h3>
              <p>
                {Number(averageRisk) > 60
                  ? 'Fraud risk is elevated. Increase manual verification for incoming invoices.'
                  : 'Overall fraud risk is stable. Continue monitoring and review flagged invoices.'}
              </p>
            </div>
          </div>
        </section>
        <section className="panel recent-alerts">
          <div className="panel-heading">
            <div>
              <h2>Recent High-Risk Alerts</h2>
              <p>Invoices requiring immediate attention</p>
            </div>
          </div>

          {highRiskAlerts.length === 0 ? (
            <div className="alerts-empty">
              No critical invoices detected.
            </div>
          ) : (
            <div className="alerts-list">
              {highRiskAlerts.map(alert => (
                <div className="alert-item" key={alert.id}>
                  <div>
                    <strong>{alert.invoice_number}</strong>
                    <p>{alert.vendor}</p>
                  </div>

                  <div className="alert-meta">
                    <span className="alert-score">{Number(alert.score).toFixed(0)}</span>
                    <span className={`history-decision ${alert.decision}`}>
                      {alert.decision.toUpperCase()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
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
                {result.investigation_report && (
                  <div className="detail-panel">

                    <h3>Fraud Investigation Report</h3>
                    <div className="detail-list">
                      <div>
                        <span>Case ID</span>
                        <strong>{result.investigation_report.case_id || 'N/A'}</strong>
                      </div>
                      <div>
                        <span>Status</span>
                        <strong>{result.investigation_report.status || 'N/A'}</strong>
                      </div>
                      <div>
                        <span>Generated At</span>
                        <strong>{result.investigation_report.generated_at || 'N/A'}</strong>
                      </div>
                      <div>
                        <span>Generated By</span>
                        <strong>{result.investigation_report.generated_by || 'N/A'}</strong>
                      </div>
                    </div>

                    <div className="detail-list">
                      <div>
                        <span>Decision</span>
                        <strong>{result.investigation_report.decision}</strong>
                      </div>
                      <div>
                        <span>Risk Score</span>
                        <strong>{result.investigation_report.risk_score}</strong>
                      </div>
                    </div>

                    <h3>AI Summary</h3>
                    <p className="decision-reason">
                      {result.investigation_report.summary}
                    </p>

                    <h3>Recommended Actions</h3>
                    <div className="signals-list">
                      {(result.investigation_report.recommended_actions || []).map((action, index) => (
                        <div className="signal" key={index}>
                          <div>
                            <strong>Action {index + 1}</strong>
                            <p>{action}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <button 
                      onClick={() => 
                        downloadInvestigationReport(
                          result.investigation_report,
                          result
                        )
                      }
                      className="analyze-button"
                    >
                      📥 Download Report
                      </button>
                  </div>
                )}
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
