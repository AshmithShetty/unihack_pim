import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { LayoutDashboard, PlusCircle, MessageSquare } from 'lucide-react'
import Home from './pages/Home'
import NewProject from './pages/NewProject'
import CommandCenter from './pages/CommandCenter'
import Dashboard from './pages/Dashboard'
import ReviewQueue from './pages/ReviewQueue'
import Chatbot from './pages/Chatbot'

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
        <nav className="bg-slate-900 text-white shadow-lg sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center gap-8">
                <Link to="/" className="flex items-center gap-2 font-bold text-xl tracking-tight">
                  <div className="bg-blue-600 p-1.5 rounded-lg">
                    <LayoutDashboard size={20} className="text-white" />
                  </div>
                  UniHack PIM
                </Link>
                <div className="hidden md:flex space-x-4">
                  <Link to="/" className="hover:bg-slate-800 px-3 py-2 rounded-md text-sm font-medium transition-colors">Projects</Link>
                  <Link to="/projects/new" className="hover:bg-slate-800 px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2">
                    <PlusCircle size={16} /> New Project
                  </Link>
                </div>
              </div>
              <div className="flex items-center">
              </div>
            </div>
          </div>
        </nav>

        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/projects/new" element={<NewProject />} />
            <Route path="/projects/:id" element={<CommandCenter />} />
            <Route path="/projects/:id/dashboard" element={<Dashboard />} />
            <Route path="/projects/:id/review" element={<ReviewQueue />} />
            <Route path="/projects/:id/chat" element={<Chatbot />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
