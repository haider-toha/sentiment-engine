'use client'

import dynamic from 'next/dynamic'
import { CountryData } from '@/lib/api'
import { Skeleton } from '@/components/ui/skeleton'

// Dynamically import Globe to avoid SSR issues with Three.js
const Globe = dynamic(() => import('./Globe'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[400px] w-full items-center justify-center">
      <Skeleton className="h-64 w-64 rounded-full" />
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
