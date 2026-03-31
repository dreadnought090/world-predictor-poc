export interface CountryMeta {
  code: string
  name: string
  flag: string
  coords: [number, number]
}

export const COUNTRIES: Record<string, CountryMeta> = {
  US: { code: 'US', name: 'United States', flag: '\u{1F1FA}\u{1F1F8}', coords: [37, -96] },
  CN: { code: 'CN', name: 'China', flag: '\u{1F1E8}\u{1F1F3}', coords: [36, 104] },
  IN: { code: 'IN', name: 'India', flag: '\u{1F1EE}\u{1F1F3}', coords: [21, 79] },
  BR: { code: 'BR', name: 'Brazil', flag: '\u{1F1E7}\u{1F1F7}', coords: [-14, -52] },
  RU: { code: 'RU', name: 'Russia', flag: '\u{1F1F7}\u{1F1FA}', coords: [62, 105] },
  JP: { code: 'JP', name: 'Japan', flag: '\u{1F1EF}\u{1F1F5}', coords: [36, 138] },
  DE: { code: 'DE', name: 'Germany', flag: '\u{1F1E9}\u{1F1EA}', coords: [51, 10] },
  GB: { code: 'GB', name: 'United Kingdom', flag: '\u{1F1EC}\u{1F1E7}', coords: [55, -3] },
  FR: { code: 'FR', name: 'France', flag: '\u{1F1EB}\u{1F1F7}', coords: [46, 2] },
  KR: { code: 'KR', name: 'South Korea', flag: '\u{1F1F0}\u{1F1F7}', coords: [36, 128] },
  AU: { code: 'AU', name: 'Australia', flag: '\u{1F1E6}\u{1F1FA}', coords: [-25, 134] },
  MX: { code: 'MX', name: 'Mexico', flag: '\u{1F1F2}\u{1F1FD}', coords: [24, -103] },
  ID: { code: 'ID', name: 'Indonesia', flag: '\u{1F1EE}\u{1F1E9}', coords: [-1, 114] },
  NG: { code: 'NG', name: 'Nigeria', flag: '\u{1F1F3}\u{1F1EC}', coords: [9, 9] },
  EG: { code: 'EG', name: 'Egypt', flag: '\u{1F1EA}\u{1F1EC}', coords: [27, 31] },
  SA: { code: 'SA', name: 'Saudi Arabia', flag: '\u{1F1F8}\u{1F1E6}', coords: [24, 45] },
  TR: { code: 'TR', name: 'Turkey', flag: '\u{1F1F9}\u{1F1F7}', coords: [39, 35] },
  PK: { code: 'PK', name: 'Pakistan', flag: '\u{1F1F5}\u{1F1F0}', coords: [30, 69] },
  PH: { code: 'PH', name: 'Philippines', flag: '\u{1F1F5}\u{1F1ED}', coords: [13, 122] },
  TH: { code: 'TH', name: 'Thailand', flag: '\u{1F1F9}\u{1F1ED}', coords: [16, 101] },
}

export const COUNTRY_LIST = Object.values(COUNTRIES)

export const CAT_COLORS: Record<string, string> = {
  ECONOMIC_POLICY: '#3b82f6',
  POLITICAL: '#8b5cf6',
  SOCIAL: '#10b981',
  MILITARY: '#ef4444',
  TECHNOLOGY: '#ec4899',
  ENVIRONMENTAL: '#22d3ee',
  HEALTH: '#f59e0b',
  TRADE: '#06b6d4',
  GENERAL: '#64748b',
}

export const CHART_COLORS = ['#3b82f6', '#22d3ee', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#f97316', '#06b6d4', '#84cc16', '#a855f7', '#14b8a6']
