'use client'

import dynamic from 'next/dynamic'
import { CountryData } from '@/lib/api'
import { Skeleton } from '@/components/ui/skeleton'

// Dynamically import Globe to avoid SSR issues with Three.js
const Globe = dynamic(() => import('./Globe'), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center">
      <Skeleton className="h-32 w-32 rounded-full lg:h-64 lg:w-64" />
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
