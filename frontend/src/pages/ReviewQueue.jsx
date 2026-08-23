import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { AlertTriangle, ArrowLeft, Check, Edit2, X, AlertCircle } from 'lucide-react'
import axios from '../api/axios'
import clsx from 'clsx'

export default function ReviewQueue() {
  const { id } = useParams()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [editingField, setEditingField] = useState(null)
  const [editValue, setEditValue] = useState('')

  useEffect(() => {
    fetchReviewRows()
  }, [id])

  const fetchReviewRows = async () => {
    try {
      // Assuming backend supports filtering by review flag, or we filter here
      const res = await axios.get(`/api/projects/${id}/rows`)
      const allRows = res.data.rows || []
      setRows(allRows.filter(r => r.needs_human_review))
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (rowId) => {
    try {
      await axios.patch(`/api/projects/${id}/rows/${rowId}`, { needs_human_review: 0 })
      setRows(rows.filter(r => r.row_id !== rowId))
    } catch (err) {
      console.error('Failed to approve', err)
    }
  }

  const startEdit = (rowId, field, currentValue) => {
    setEditingField(`${rowId}-${field}`)
    setEditValue(currentValue || '')
  }

  const saveEdit = async (rowId, field) => {
    try {
      await axios.patch(`/api/projects/${id}/rows/${rowId}`, { [field]: editValue })
      setRows(rows.map(r => {
        if (r.row_id === rowId) {
          return { ...r, [field]: editValue }
        }
        return r
      }))
      setEditingField(null)
    } catch (err) {
      console.error('Failed to save edit', err)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-slate-500">Loading review queue...</div>
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
          <Link to={`/projects/${id}/dashboard`} className="hover:text-blue-600 flex items-center gap-1">
            <ArrowLeft size={14} /> Back to Dashboard
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-amber-100 p-2 rounded-lg">
            <AlertTriangle className="text-amber-600" size={24} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Human Review Queue</h1>
            <p className="text-sm text-slate-500">Resolve flagged fields or low confidence records</p>
          </div>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-50 mb-4">
            <Check size={32} className="text-green-500" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">Queue Empty</h3>
          <p className="text-slate-500 mb-6">All rows have passed validation successfully.</p>
          <Link to={`/projects/${id}`} className="text-blue-600 font-medium hover:text-blue-700">Return to grid &rarr;</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {rows.map(row => (
            <div key={row.row_id} className="bg-white rounded-xl border border-amber-200 overflow-hidden shadow-sm">
              <div className="px-6 py-4 bg-amber-50 border-b border-amber-100 flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-amber-900 text-lg">{row.Mfg_Part_Num}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <AlertCircle size={14} className="text-amber-700" />
                    <p className="text-sm text-amber-800 font-medium">Reason: {row.review_reason || 'Low confidence score (<0.6)'}</p>
                  </div>
                </div>
                <button 
                  onClick={() => handleApprove(row.row_id)}
                  className="bg-white hover:bg-green-50 text-green-700 border border-green-200 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2 text-sm"
                >
                  <Check size={16} /> Approve & Clear
                </button>
              </div>

              <div className="p-6">
                <h4 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wider">Key Fields Review</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Manufacturer */}
                  <div className="p-3 border border-slate-200 rounded-lg bg-slate-50 relative group">
                    <div className="text-xs font-semibold text-slate-500 mb-1">MANUFACTURER_NAME</div>
                    {editingField === `${row.row_id}-MANUFACTURER_NAME` ? (
                      <div className="flex items-center gap-2">
                        <input 
                          autoFocus
                          className="flex-1 text-sm border-slate-300 rounded p-1" 
                          value={editValue} 
                          onChange={e => setEditValue(e.target.value)} 
                        />
                        <button onClick={() => saveEdit(row.row_id, 'MANUFACTURER_NAME')} className="text-green-600"><Check size={16}/></button>
                        <button onClick={() => setEditingField(null)} className="text-slate-400"><X size={16}/></button>
                      </div>
                    ) : (
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-900">{row.MANUFACTURER_NAME || 'None'}</span>
                        <button onClick={() => startEdit(row.row_id, 'MANUFACTURER_NAME', row.MANUFACTURER_NAME)} className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-blue-600 transition-opacity">
                          <Edit2 size={14} />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Brand */}
                  <div className="p-3 border border-slate-200 rounded-lg bg-slate-50 relative group">
                    <div className="text-xs font-semibold text-slate-500 mb-1">BRAND_NAME</div>
                    {editingField === `${row.row_id}-BRAND_NAME` ? (
                      <div className="flex items-center gap-2">
                        <input 
                          autoFocus
                          className="flex-1 text-sm border-slate-300 rounded p-1" 
                          value={editValue} 
                          onChange={e => setEditValue(e.target.value)} 
                        />
                        <button onClick={() => saveEdit(row.row_id, 'BRAND_NAME')} className="text-green-600"><Check size={16}/></button>
                        <button onClick={() => setEditingField(null)} className="text-slate-400"><X size={16}/></button>
                      </div>
                    ) : (
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-900">{row.BRAND_NAME || 'None'}</span>
                        <button onClick={() => startEdit(row.row_id, 'BRAND_NAME', row.BRAND_NAME)} className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-blue-600 transition-opacity">
                          <Edit2 size={14} />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Invoice Desc */}
                  <div className={clsx("p-3 border rounded-lg relative group md:col-span-2", row.INVOICE_DESC?.length > 40 ? "border-red-300 bg-red-50" : "border-slate-200 bg-slate-50")}>
                    <div className="flex justify-between">
                      <div className="text-xs font-semibold text-slate-500 mb-1">INVOICE_DESC</div>
                      <div className={clsx("text-xs", (row.INVOICE_DESC?.length || 0) > 40 ? "text-red-600 font-bold" : "text-slate-400")}>
                        {row.INVOICE_DESC?.length || 0}/40 chars
                      </div>
                    </div>
                    
                    {editingField === `${row.row_id}-INVOICE_DESC` ? (
                      <div className="flex items-center gap-2">
                        <input 
                          autoFocus
                          className="flex-1 text-sm border-slate-300 rounded p-1 uppercase font-mono" 
                          value={editValue} 
                          onChange={e => setEditValue(e.target.value.toUpperCase())} 
                        />
                        <button onClick={() => saveEdit(row.row_id, 'INVOICE_DESC')} className="text-green-600"><Check size={16}/></button>
                        <button onClick={() => setEditingField(null)} className="text-slate-400"><X size={16}/></button>
                      </div>
                    ) : (
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-slate-900 font-mono">{row.INVOICE_DESC || 'None'}</span>
                        <button onClick={() => startEdit(row.row_id, 'INVOICE_DESC', row.INVOICE_DESC)} className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-blue-600 transition-opacity">
                          <Edit2 size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
