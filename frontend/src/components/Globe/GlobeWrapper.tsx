'use client'

import dynamic from 'next/dynamic'
import { CountryData } from '@/lib/api'
import { Skeleton } from '@/components/ui/skeleton'

// Dynamically import Globe to avoid SSR issues with Three.js
const Globe = dynamic(() => import('./Globe'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[400px] flex items-center justify-center">
      <Skeleton className="w-64 h-64 rounded-full" />
    </div>
  ),
})

interface GlobeWrapperProps {
  countries: CountryData[]
  onCountrySelect: (countryCode: string | null) => void
  selectedCountry: string | null
}

export default function GlobeWrapper({
  countries,
  onCountrySelect,
  selectedCountry,
}: GlobeWrapperProps) {
  return (
    <Globe
      countries={countries}
      onCountrySelect={onCountrySelect}
      selectedCountry={selectedCountry}
    />
  )
}

