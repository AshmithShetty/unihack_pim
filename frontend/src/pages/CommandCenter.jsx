import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Activity, Download, LayoutList, ChevronRight, X, Loader2, Info, FileText, Settings, Image as ImageIcon, Shield, AlertTriangle, MessageSquare } from 'lucide-react'
import axios from '../api/axios'
import clsx from 'clsx'
import { FixedSizeList as List } from 'react-window'

export default function CommandCenter() {
  const { id } = useParams()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedRow, setSelectedRow] = useState(null)
  const [activeTab, setActiveTab] = useState('identity')
  const [auditData, setAuditData] = useState([])

  useEffect(() => {
    fetchRows()
    const interval = setInterval(fetchRows, 5000) // Poll for updates (WebSocket is better but this is fallback)
    return () => clearInterval(interval)
  }, [id])

  useEffect(() => {
    if (activeTab === 'audit' && selectedRow) {
      axios.get(`/api/rows/${selectedRow.row_id}/audit`)
        .then(res => setAuditData(res.data.audit))
        .catch(err => console.error(err))
    }
  }, [activeTab, selectedRow])

  const fetchRows = async () => {
    try {
      const res = await axios.get(`/api/projects/${id}/rows`)
      setRows(res.data.rows || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = () => {
    window.location.href = `/api/projects/${id}/export`
  }

  const renderRowItem = (row) => {
    const isSelected = selectedRow?.row_id === row.row_id
    
    const rowTitle = row.Mfg_Part_Num || row.PART_NUMBER || row['SKU - MY_PART_NUMBER'] || row.UPC || row.GTIN || 'Unknown Item'
    const rowSubtitle = row.BRAND_NAME || row.MANUFACTURER_NAME || row.Part_Manuf || 'Unknown Brand'
    
    return (
      <div 
        key={row.row_id}
        onClick={() => setSelectedRow(row)}
        className={clsx(
          "flex items-center px-4 py-3 border-b border-slate-100 cursor-pointer transition-colors hover:bg-slate-50",
          isSelected ? "bg-blue-50 border-l-4 border-l-blue-600" : "border-l-4 border-l-transparent"
        )}
      >
        <div className="flex-1 min-w-0 pr-4">
          <div className="flex justify-between items-center mb-1">
            <span className="font-semibold text-slate-900 truncate" title={rowTitle}>
              {rowTitle}
            </span>
            <div className="flex items-center gap-2">
              {row.needs_human_review ? (
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700 uppercase">Review</span>
              ) : null}
              <span className={clsx(
                "w-2 h-2 rounded-full",
                row.status === 'done' ? "bg-green-500" : 
                row.status === 'running' ? "bg-blue-500 animate-pulse" : 
                row.status === 'failed' ? "bg-red-500" : "bg-slate-300"
              )}></span>
            </div>
          </div>
          <div className="text-xs text-slate-500 truncate flex justify-between">
            <span>{rowSubtitle}</span>
            <span className={clsx("font-medium", row.confidence_score > 0.8 ? "text-green-600" : "text-amber-600")}>
              {row.confidence_score ? `${Math.round(row.confidence_score * 100)}%` : '-'}
            </span>
          </div>
        </div>
        <ChevronRight size={16} className={clsx("text-slate-400 transition-transform", isSelected && "text-blue-600 translate-x-1")} />
      </div>
    )
  }

  const renderTabContent = () => {
    if (!selectedRow) return null

    const tabs = {
      identity: [
        { label: 'Manufacturer Name', value: selectedRow.MANUFACTURER_NAME },
        { label: 'Brand Name', value: selectedRow.BRAND_NAME },
        { label: 'Trade Name', value: selectedRow.TRADE_NAME },
        { label: 'UNSPSC', value: selectedRow.UNSPSC },
        { label: 'Classpath', value: selectedRow.Classpath },
      ],
      descriptions: [
        { label: 'Short Description', value: selectedRow.SHORT_DESC },
        { label: 'Long Description 1', value: selectedRow.LONG_DESC1 },
        { label: 'Invoice Description', value: selectedRow.INVOICE_DESC },
        { label: 'Mobile Description', value: selectedRow.MOBILE_DESC },
        { label: 'Retail Description', value: selectedRow.RETAIL_DESC },
        { label: 'Marketing Description', value: selectedRow.MARKETING_DESCRIPTION },
      ],
      features: Array.from({ length: 20 }).map((_, i) => ({
        label: `Feature ${i+1}`, value: selectedRow[`ITEM_FEATURES_${i+1}`]
      })).filter(f => f.value),
      specs: Array.from({ length: 50 }).map((_, i) => ({
        label: selectedRow[`ATTRIBUTE_LABEL ${i+1}`], 
        value: selectedRow[`ATTRIBUTE_VALUE ${i+1}`],
        uom: selectedRow[`ATTRIBUTE_UOM ${i+1}`]
      })).filter(s => s.label || s.value),
      media: [
        { label: 'MFR URL', value: selectedRow['MFR URL'], isLink: true },
        { label: 'Ref URL 1', value: selectedRow['Ref URL 1'], isLink: true },
        { label: 'Ref URL 2', value: selectedRow['Ref URL 2'], isLink: true },
        { label: 'Product Image', value: selectedRow['Product Image'] },
        { label: 'Spec Sheet', value: selectedRow['Specification Sheet'] },
      ].filter(m => m.value)
    }

    const currentFields = tabs[activeTab] || []

    return (
      <div className="p-6 space-y-4">
        {currentFields.length === 0 && activeTab !== 'audit' ? (
          <p className="text-slate-500 italic text-sm">No data available for this section.</p>
        ) : activeTab === 'audit' ? (
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <th className="py-2 px-3">Field Name</th>
                <th className="py-2 px-3">Source Type</th>
                <th className="py-2 px-3">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {auditData.map((f, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-medium text-slate-900">{f.field_name}</td>
                  <td className="py-2 px-3 text-slate-700">
                    <span className="px-2 py-1 bg-slate-100 rounded text-xs font-mono">{f.source_type}</span>
                  </td>
                  <td className="py-2 px-3 text-slate-500">
                    <span className={clsx("font-bold", f.field_confidence > 0.9 ? "text-green-600" : "text-amber-600")}>
                      {Math.round(f.field_confidence * 100)}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : activeTab === 'specs' ? (
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <th className="py-2 px-3">Label</th>
                <th className="py-2 px-3">Value</th>
                <th className="py-2 px-3">UOM</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {currentFields.map((f, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="py-2 px-3 font-medium text-slate-900">{f.label || '-'}</td>
                  <td className="py-2 px-3 text-slate-700">{f.value || '-'}</td>
                  <td className="py-2 px-3 text-slate-500">{f.uom || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="space-y-4">
            {currentFields.map((f, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                <div className="text-xs font-semibold text-slate-500 mb-1 uppercase tracking-wider">{f.label}</div>
                {f.isLink ? (
                  <a href={f.value} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline break-all">
                    {f.value}
                  </a>
                ) : (
                  <div className="text-sm text-slate-900">{f.value || <span className="text-slate-400 italic">None</span>}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  const isComplete = rows.length > 0 && rows.every(r => r.status === 'done')

  if (loading && rows.length === 0) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="animate-spin text-slate-400" size={32} /></div>
  }

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Command Center</h1>
          <p className="text-sm text-slate-500">Project #{id}</p>
        </div>
        <div className="flex gap-3">
          {isComplete ? (
            <Link to={`/projects/${id}/chat`} className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2">
              <MessageSquare size={18} />
              Data Chatbot
            </Link>
          ) : (
            <button disabled title="Available once enrichment is 100% complete" className="bg-slate-300 text-slate-500 cursor-not-allowed px-4 py-2 rounded-lg font-medium shadow-sm flex items-center gap-2">
              <MessageSquare size={18} />
              Data Chatbot
            </button>
          )}
          <Link to={`/projects/${id}/dashboard`} className="bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2">
            <Activity size={18} />
            Live Dashboard
          </Link>
          <button onClick={handleExport} className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2">
            <Download size={18} />
            Export CSV
          </button>
        </div>
      </div>

      <div className="flex-1 flex gap-6 overflow-hidden">
        {/* Left Panel: Virtualized List */}
        <div className="w-1/3 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden shrink-0">
          <div className="px-4 py-3 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <h2 className="font-semibold text-slate-800 flex items-center gap-2">
              <LayoutList size={18} />
              Master Data Grid
            </h2>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-bold">{rows.length} rows</span>
          </div>
          <div className="flex-1 bg-white scrollbar-thin scrollbar-thumb-slate-300">
            {rows.length > 0 && (
              <List
                height={window.innerHeight - 200}
                itemCount={rows.length}
                itemSize={80}
                width="100%"
              >
                {({ index, style }) => (
                  <div style={style}>
                    {renderRowItem(rows[index])}
                  </div>
                )}
              </List>
            )}
          </div>
        </div>

        {/* Right Panel: Side Panel */}
        <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden">
          {selectedRow ? (
            <>
              <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex justify-between items-start">
                <div>
                  <h2 className="text-xl font-bold text-slate-900 mb-1">{selectedRow.Mfg_Part_Num}</h2>
                  <p className="text-sm text-slate-600">{selectedRow.Part_Desc}</p>
                </div>
                <button onClick={() => setSelectedRow(null)} className="p-1 hover:bg-slate-200 rounded-md text-slate-400 hover:text-slate-600 transition-colors">
                  <X size={20} />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-slate-200 px-2 overflow-x-auto">
                {[
                  { id: 'identity', label: 'Identity', icon: Info },
                  { id: 'descriptions', label: 'Descriptions', icon: FileText },
                  { id: 'features', label: 'Features', icon: LayoutList },
                  { id: 'specs', label: 'Tech Specs', icon: Settings },
                  { id: 'media', label: 'Media & Docs', icon: ImageIcon },
                  { id: 'audit', label: 'Audit', icon: Shield },
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={clsx(
                      "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                      activeTab === tab.id 
                        ? "border-blue-600 text-blue-600" 
                        : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                    )}
                  >
                    <tab.icon size={16} />
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto bg-white">
                {renderTabContent()}
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8 text-center">
              <Shield size={64} className="mb-4 text-slate-200" />
              <h3 className="text-lg font-medium text-slate-600 mb-1">No row selected</h3>
              <p className="text-sm">Click on a row in the Master Data Grid to view its fully enriched golden record properties.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
