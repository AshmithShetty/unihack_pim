import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FolderKanban, CheckCircle2, Clock, AlertCircle, Play, Loader2 } from 'lucide-react'
import axios from '../api/axios'
import { useStore } from '../store'
import clsx from 'clsx'

export default function Home() {
  const { projects, setProjects } = useStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const res = await axios.get('/api/projects')
      setProjects(res.data.projects || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getStatusConfig = (status) => {
    switch (status) {
      case 'done': return { icon: CheckCircle2, color: 'text-green-500', bg: 'bg-green-50' }
      case 'running': return { icon: Loader2, color: 'text-blue-500', bg: 'bg-blue-50', animate: 'animate-spin' }
      case 'failed': return { icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-50' }
      default: return { icon: Clock, color: 'text-slate-500', bg: 'bg-slate-50' }
    }
  }

  if (loading) {
    return <div className="flex justify-center items-center h-64"><Loader2 className="animate-spin text-slate-400" size={32} /></div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Projects</h1>
        <Link to="/projects/new" className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition-colors shadow-sm flex items-center gap-2">
          <FolderKanban size={18} />
          New Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center shadow-sm">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-50 mb-4">
            <FolderKanban size={32} className="text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No projects yet</h3>
          <p className="text-slate-500 mb-6">Upload a supplier CSV to create your first PIM enrichment project.</p>
          <Link to="/projects/new" className="text-blue-600 font-medium hover:text-blue-700">Get started &rarr;</Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => {
            const statusConfig = getStatusConfig(project.status)
            const StatusIcon = statusConfig.icon
            
            return (
              <Link key={project.project_id} to={`/projects/${project.project_id}`} className="block group">
                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all hover:border-blue-300">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="font-semibold text-lg text-slate-900 line-clamp-1 group-hover:text-blue-600 transition-colors">
                      {project.project_name}
                    </h3>
                    <div className={clsx("p-2 rounded-lg", statusConfig.bg)}>
                      <StatusIcon size={20} className={clsx(statusConfig.color, statusConfig.animate)} />
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">File</span>
                      <span className="font-medium text-slate-700 truncate max-w-[150px]" title={project.filename}>{project.filename || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Progress</span>
                      <span className="font-medium text-slate-700">
                        {project.processed_rows || 0} / {project.total_rows || 0}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Confidence</span>
                      <span className={clsx("font-medium", project.avg_confidence > 0.8 ? "text-green-600" : "text-amber-600")}>
                        {project.avg_confidence ? (project.avg_confidence * 100).toFixed(1) + '%' : 'N/A'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-5 pt-4 border-t border-slate-100 flex justify-between items-center text-sm text-blue-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    View Dashboard
                    <Play size={14} />
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
