import { create } from 'zustand'

interface UIStore {
  searchQuery: string
  sortColumn: string
  sortDir: 'asc' | 'desc'
  comparisonCountries: string[]
  setSearch: (q: string) => void
  setSort: (col: string) => void
  toggleComparison: (code: string) => void
  clearComparison: () => void
}

export const useUIStore = create<UIStore>((set) => ({
  searchQuery: '',
  sortColumn: 'revolution_risk',
  sortDir: 'desc',
  comparisonCountries: [],
  setSearch: (q) => set({ searchQuery: q }),
  setSort: (col) =>
    set((s) => ({
      sortColumn: col,
      sortDir: s.sortColumn === col && s.sortDir === 'desc' ? 'asc' : 'desc',
    })),
  toggleComparison: (code) =>
    set((s) => {
      const has = s.comparisonCountries.includes(code)
      if (has) return { comparisonCountries: s.comparisonCountries.filter((c) => c !== code) }
      if (s.comparisonCountries.length >= 3) return s
      return { comparisonCountries: [...s.comparisonCountries, code] }
    }),
  clearComparison: () => set({ comparisonCountries: [] }),
}))
