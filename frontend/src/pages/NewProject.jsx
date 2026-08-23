import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { UploadCloud, FileSpreadsheet, ArrowRight, CheckCircle2, Loader2, AlertCircle } from 'lucide-react'
import axios from '../api/axios'

export default function NewProject() {
  const navigate = useNavigate()
  const [projectName, setProjectName] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [mappingProposal, setMappingProposal] = useState(null)
  const [projectId, setProjectId] = useState(null)
  const [confirming, setConfirming] = useState(false)

  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles?.length > 0) {
      setFile(acceptedFiles[0])
      setError('')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1
  })

  const handleUpload = async () => {
    if (!projectName.trim()) {
      setError('Please enter a project name')
      return
    }
    if (!file) {
      setError('Please select a CSV file')
      return
    }

    setUploading(true)
    setError('')

    try {
      // 1. Create project
      const createRes = await axios.post('/api/projects', { project_name: projectName })
      const id = createRes.data.project_id
      setProjectId(id)

      // 2. Upload file & get mapping
      const formData = new FormData()
      formData.append('file', file)
      
      const uploadRes = await axios.post(`/api/projects/${id}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      
      setMappingProposal(uploadRes.data.mapping_proposal)
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || err.message || 'An error occurred during upload')
    } finally {
      setUploading(false)
    }
  }

  const handleConfirm = async () => {
    setConfirming(true)
    try {
      await axios.post(`/api/projects/${projectId}/confirm`, mappingProposal)
      navigate(`/projects/${projectId}`)
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || err.message || 'Failed to confirm mapping')
      setConfirming(false)
    }
  }

  const handleMappingChange = (supplierCol, newTarget) => {
    setMappingProposal(prev => ({
      ...prev,
      [supplierCol]: {
        ...prev[supplierCol],
        mapped_target: newTarget
      }
    }))
  }

  if (mappingProposal) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-200 bg-slate-50 flex justify-between items-center">
            <div>
              <h2 className="text-lg font-bold text-slate-900">AI Column Mapping</h2>
              <p className="text-sm text-slate-500">Review and confirm the Golden Record mappings</p>
            </div>
            <button 
              onClick={handleConfirm}
              disabled={confirming}
              className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              {confirming ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle2 size={18} />}
              Confirm & Start Enrichment
            </button>
          </div>
          <div className="p-0">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-sm font-medium text-slate-600">
                  <th className="py-3 px-6">Supplier Column</th>
                  <th className="py-3 px-6">Target Column</th>
                  <th className="py-3 px-6">Confidence</th>
                  <th className="py-3 px-6">AI Reasoning</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {Object.entries(mappingProposal).map(([col, data]) => (
                  <tr key={col} className="hover:bg-slate-50">
                    <td className="py-4 px-6 font-medium text-slate-900">{col}</td>
                    <td className="py-4 px-6">
                      <select 
                        value={data.mapped_target}
                        onChange={(e) => handleMappingChange(col, e.target.value)}
                        className="w-full border-slate-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm bg-white p-2 border"
                      >
                        <option value={data.mapped_target}>{data.mapped_target}</option>
                        <option value="__IGNORE__">__IGNORE__</option>
                        <option value="__CONTEXT__">__CONTEXT__</option>
                      </select>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-slate-200 rounded-full h-2 max-w-[60px]">
                          <div 
                            className={`h-2 rounded-full ${data.confidence > 0.8 ? 'bg-green-500' : data.confidence > 0.5 ? 'bg-amber-500' : 'bg-red-500'}`} 
                            style={{ width: `${Math.max(0, Math.min(100, data.confidence * 100))}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-slate-500 font-medium">{Math.round(data.confidence * 100)}%</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-sm text-slate-600 italic">
                      {data.reasoning}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">New Project</h1>
        <p className="text-slate-500">Upload a supplier CSV to map and enrich product data.</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-lg flex items-start gap-3 border border-red-200">
          <AlertCircle size={20} className="mt-0.5" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Project Name</label>
          <input 
            type="text" 
            placeholder="e.g., Milwaukee Tools October Batch"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            className="w-full border-slate-300 rounded-lg shadow-sm focus:border-blue-500 focus:ring-blue-500 p-3 border text-slate-900"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">Supplier CSV File</label>
          <div 
            {...getRootProps()} 
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-slate-400 bg-slate-50 hover:bg-slate-100'
            }`}
          >
            <input {...getInputProps()} />
            {file ? (
              <div className="flex flex-col items-center text-blue-600">
                <FileSpreadsheet size={48} className="mb-3 opacity-80" />
                <p className="font-medium text-lg">{file.name}</p>
                <p className="text-sm text-blue-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="flex flex-col items-center text-slate-500">
                <UploadCloud size={48} className="mb-3 text-slate-400" />
                <p className="font-medium text-lg text-slate-700">Drag & drop CSV file here</p>
                <p className="text-sm mt-1">or click to browse</p>
              </div>
            )}
          </div>
        </div>

        <div className="pt-4 flex justify-end">
          <button 
            onClick={handleUpload}
            disabled={!file || !projectName.trim() || uploading}
            className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto justify-center"
          >
            {uploading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Analyzing mapping...
              </>
            ) : (
              <>
                Upload & Map Columns
                <ArrowRight size={20} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
