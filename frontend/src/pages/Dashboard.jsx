import { useEffect, useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts'
import { Activity, ArrowLeft, Users, Zap, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react'
import axios from '../api/axios'
import clsx from 'clsx'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function Dashboard() {
  const { id } = useParams()
  const [rows, setRows] = useState([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Initial fetch
    axios.get(`/api/projects/${id}/rows`).then(res => setRows(res.data.rows || []))

    // Set up WebSocket
    let wsUrl = ''
    if (import.meta.env.VITE_API_URL) {
      const backendUrl = new URL(import.meta.env.VITE_API_URL)
      const wsProtocol = backendUrl.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${wsProtocol}//${backendUrl.host}/ws/projects/${id}`
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      wsUrl = `${protocol}//${window.location.host}/ws/projects/${id}`
    }
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.message !== 'Connected') {
          // If the backend actually sends row updates in Phase 5/6, we'd merge them here
          // For now, just re-fetch to keep it simple and accurate
          axios.get(`/api/projects/${id}/rows`).then(res => setRows(res.data.rows || []))
        }
      } catch (e) {
        console.error(e)
      }
    }

    const interval = setInterval(() => {
      axios.get(`/api/projects/${id}/rows`).then(res => setRows(res.data.rows || []))
    }, 5000)

    return () => {
      ws.close()
      clearInterval(interval)
    }
  }, [id])

  const metrics = useMemo(() => {
    const total = rows.length
    if (total === 0) return null

    const completed = rows.filter(r => r.status === 'done').length
    const reviewNeeded = rows.filter(r => r.needs_human_review).length
    const avgConf = rows.reduce((acc, r) => acc + (r.confidence_score || 0), 0) / total

    const categoryCounts = rows.reduce((acc, r) => {
      let category = r.Class || r.Dept || 'Uncategorized'
      if (typeof category !== 'string' || category.trim() === '') {
        category = 'Uncategorized'
      }
      acc[category] = (acc[category] || 0) + 1
      return acc
    }, {})

    let categoryData = Object.entries(categoryCounts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)

    if (categoryData.length > 4) {
      const top3 = categoryData.slice(0, 3)
      const other = categoryData.slice(3).reduce((sum, item) => sum + item.value, 0)
      categoryData = [...top3, { name: 'Other', value: other }]
    }

    const confidenceData = [
      { name: '90-100%', value: rows.filter(r => r.confidence_score >= 0.9).length },
      { name: '70-89%', value: rows.filter(r => r.confidence_score >= 0.7 && r.confidence_score < 0.9).length },
      { name: '<70%', value: rows.filter(r => r.confidence_score < 0.7).length },
    ]

    return { total, completed, reviewNeeded, avgConf, categoryData, confidenceData }
  }, [rows])

  if (!metrics) {
    return <div className="p-8 text-center text-slate-500">Loading metrics...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
            <Link to={`/projects/${id}`} className="hover:text-blue-600 flex items-center gap-1">
              <ArrowLeft size={14} /> Back to Grid
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Activity size={24} className="text-blue-600" />
            Live Enrichment Metrics
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-sm font-medium px-3 py-1 bg-slate-100 rounded-full border border-slate-200">
            <span className={clsx("w-2 h-2 rounded-full", isConnected ? "bg-green-500 animate-pulse" : "bg-slate-400")}></span>
            {isConnected ? 'Live WebSocket Connected' : 'Polling Mode'}
          </span>
          <Link to={`/projects/${id}/review`} className="bg-amber-100 hover:bg-amber-200 text-amber-800 border border-amber-200 px-4 py-2 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2">
            <AlertTriangle size={18} />
            Review Queue ({metrics.reviewNeeded})
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-slate-500 text-sm font-medium">Processing Progress</h3>
            <Zap size={18} className="text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-slate-900">{metrics.completed} <span className="text-lg text-slate-400 font-normal">/ {metrics.total}</span></p>
          <div className="w-full bg-slate-100 rounded-full h-1.5 mt-4">
            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${(metrics.completed / metrics.total) * 100}%` }}></div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-slate-500 text-sm font-medium">Avg Confidence</h3>
            <ShieldCheck size={18} className={metrics.avgConf > 0.8 ? 'text-green-500' : 'text-amber-500'} />
          </div>
          <p className="text-3xl font-bold text-slate-900">{(metrics.avgConf * 100).toFixed(1)}%</p>
          <p className="text-sm text-slate-500 mt-2">Across all mapped fields</p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-slate-500 text-sm font-medium">Golden Records</h3>
            <CheckCircle2 size={18} className="text-green-500" />
          </div>
          <p className="text-3xl font-bold text-slate-900">{metrics.completed - metrics.reviewNeeded}</p>
          <p className="text-sm text-slate-500 mt-2">Passed all validations</p>
        </div>

        <div className="bg-white rounded-xl border border-amber-200 p-5 shadow-sm bg-amber-50">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-amber-800 text-sm font-medium">Needs Human Review</h3>
            <Users size={18} className="text-amber-600" />
          </div>
          <p className="text-3xl font-bold text-amber-900">{metrics.reviewNeeded}</p>
          <p className="text-sm text-amber-700 mt-2">Flagged for manual inspection</p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-semibold text-slate-900 mb-6">Confidence Score Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.confidenceData} margin={{ top: 5, right: 30, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} />
                <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col">
          <h3 className="font-semibold text-slate-900 mb-2">Detected Categories</h3>
          <div className="flex-1 min-h-[250px] relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {metrics.categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
              <span className="block text-2xl font-bold text-slate-900">{metrics.total}</span>
              <span className="block text-xs text-slate-500 uppercase">Products</span>
            </div>
          </div>
          <div className="flex justify-center gap-4 mt-2">
            {metrics.categoryData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-xs text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                {entry.name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
