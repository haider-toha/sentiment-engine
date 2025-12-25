/**
 * Country code to name mappings and utilities
 */

export const COUNTRY_NAMES: Record<string, string> = {
  US: 'United States',
  GB: 'United Kingdom',
  CA: 'Canada',
  AU: 'Australia',
  DE: 'Germany',
  FR: 'France',
  IT: 'Italy',
  ES: 'Spain',
  NL: 'Netherlands',
  BE: 'Belgium',
  SE: 'Sweden',
  NO: 'Norway',
  DK: 'Denmark',
  FI: 'Finland',
  PL: 'Poland',
  CZ: 'Czech Republic',
  AT: 'Austria',
  CH: 'Switzerland',
  IE: 'Ireland',
  PT: 'Portugal',
  GR: 'Greece',
  RU: 'Russia',
  UA: 'Ukraine',
  TR: 'Turkey',
  IN: 'India',
  CN: 'China',
  JP: 'Japan',
  KR: 'South Korea',
  TW: 'Taiwan',
  HK: 'Hong Kong',
  SG: 'Singapore',
  MY: 'Malaysia',
  ID: 'Indonesia',
  TH: 'Thailand',
  VN: 'Vietnam',
  PH: 'Philippines',
  BR: 'Brazil',
  MX: 'Mexico',
  AR: 'Argentina',
  CL: 'Chile',
  CO: 'Colombia',
  PE: 'Peru',
  ZA: 'South Africa',
  NG: 'Nigeria',
  KE: 'Kenya',
  EG: 'Egypt',
  IL: 'Israel',
  SA: 'Saudi Arabia',
  AE: 'UAE',
  QA: 'Qatar',
  NZ: 'New Zealand',
}

export function getCountryName(code: string): string {
  return COUNTRY_NAMES[code.toUpperCase()] || code
}

/**
 * Country center coordinates for globe positioning
 */
export const COUNTRY_CENTERS: Record<string, [number, number]> = {
  US: [-95.7, 37.1],
  GB: [-3.4, 55.4],
  CA: [-106.3, 56.1],
  AU: [133.8, -25.3],
  DE: [10.5, 51.2],
  FR: [2.2, 46.2],
  IT: [12.6, 41.9],
  ES: [-3.7, 40.5],
  JP: [138.3, 36.2],
  CN: [104.2, 35.9],
  IN: [78.9, 20.6],
  BR: [-51.9, -14.2],
  RU: [105.3, 61.5],
  KR: [127.8, 35.9],
  MX: [-102.6, 23.6],
}

export function getCountryCenter(code: string): [number, number] | null {
  return COUNTRY_CENTERS[code.toUpperCase()] || null
}
