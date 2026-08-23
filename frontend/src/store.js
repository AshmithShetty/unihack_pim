import { create } from 'zustand'

export const useStore = create((set) => ({
  projects: [],
  currentProject: null,
  dashboardMetrics: null,
  
  setProjects: (projects) => set({ projects }),
  setCurrentProject: (project) => set({ currentProject: project }),
  setDashboardMetrics: (metrics) => set({ dashboardMetrics: metrics }),
}))
