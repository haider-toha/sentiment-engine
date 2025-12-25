'use client'

import { useRef, useMemo, useState, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Sphere, useTexture } from '@react-three/drei'
import * as THREE from 'three'
import { CountryData } from '@/lib/api'
import { interpolateSentimentColor } from '@/lib/utils'

interface GlobeProps {
  countries: CountryData[]
  onCountrySelect: (countryCode: string | null) => void
  selectedCountry: string | null
}

// Earth texture - local file in public folder
const EARTH_TEXTURE_URL = '/earth-map.jpg'

function EarthSphere() {
  const texture = useTexture(EARTH_TEXTURE_URL)

  return (
    <Sphere args={[1, 64, 64]}>
      <meshStandardMaterial map={texture} roughness={0.8} metalness={0.1} />
    </Sphere>
  )
}

function FallbackSphere() {
  return (
    <Sphere args={[1, 64, 64]}>
      <meshStandardMaterial color="#1e3a5f" roughness={0.8} metalness={0.1} />
    </Sphere>
  )
}

function GlobeMesh({ countries, onCountrySelect, selectedCountry }: GlobeProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState<string | null>(null)

  // Slow rotation
  useFrame((state, delta) => {
    if (meshRef.current && !hovered) {
      meshRef.current.rotation.y += delta * 0.03
    }
  })

  // Create country markers
  const markers = useMemo(() => {
    // Simple lat/long to 3D position conversion
    const latLongToVector3 = (lat: number, lon: number, radius: number) => {
      const phi = (90 - lat) * (Math.PI / 180)
      const theta = (lon + 180) * (Math.PI / 180)

      return new THREE.Vector3(
        -radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.cos(phi),
        radius * Math.sin(phi) * Math.sin(theta)
      )
    }

    // Country approximate centers
    const countryCenters: Record<string, [number, number]> = {
      US: [37.1, -95.7],
      GB: [55.4, -3.4],
      CA: [56.1, -106.3],
      AU: [-25.3, 133.8],
      DE: [51.2, 10.5],
      FR: [46.2, 2.2],
      IT: [41.9, 12.6],
      ES: [40.5, -3.7],
      JP: [36.2, 138.3],
      CN: [35.9, 104.2],
      IN: [20.6, 78.9],
      BR: [-14.2, -51.9],
      RU: [61.5, 105.3],
      KR: [35.9, 127.8],
      MX: [23.6, -102.6],
      NL: [52.1, 5.3],
      SE: [60.1, 18.6],
      NO: [60.5, 8.5],
      PL: [51.9, 19.1],
      UA: [48.4, 31.2],
      ZA: [-30.6, 22.9],
      NG: [9.1, 8.7],
      EG: [26.8, 30.8],
      SA: [23.9, 45.1],
      AE: [23.4, 53.8],
      SG: [1.4, 103.8],
      ID: [-0.8, 113.9],
      TH: [15.9, 100.9],
      VN: [14.1, 108.3],
      PH: [12.9, 121.8],
      AR: [-38.4, -63.6],
      CL: [-35.7, -71.5],
      CO: [4.6, -74.3],
      PE: [-9.2, -75.0],
      QA: [25.4, 51.2],
    }

    return countries
      .map((country) => {
        const center = countryCenters[country.country_code]
        if (!center) return null

        const position = latLongToVector3(center[0], center[1], 1.025)
        const color = interpolateSentimentColor(country.sentiment_score)
        const isSelected = selectedCountry === country.country_code
        const isHovered = hovered === country.country_code

        return {
          ...country,
          position,
          color,
          isSelected,
          isHovered,
          scale: isSelected || isHovered ? 0.045 : 0.028,
        }
      })
      .filter(Boolean)
  }, [countries, selectedCountry, hovered])

  return (
    <group ref={meshRef}>
      {/* Globe sphere with Earth texture */}
      <Suspense fallback={<FallbackSphere />}>
        <EarthSphere />
      </Suspense>

      {/* Country markers */}
      {markers.map(
        (marker) =>
          marker && (
            <mesh
              key={marker.country_code}
              position={marker.position}
              onPointerOver={(e) => {
                e.stopPropagation()
                setHovered(marker.country_code)
                document.body.style.cursor = 'pointer'
              }}
              onPointerOut={() => {
                setHovered(null)
                document.body.style.cursor = 'auto'
              }}
              onClick={(e) => {
                e.stopPropagation()
                onCountrySelect(
                  selectedCountry === marker.country_code ? null : marker.country_code
                )
              }}
            >
              <sphereGeometry args={[marker.scale, 16, 16]} />
              <meshStandardMaterial
                color={marker.color}
                emissive={marker.color}
                emissiveIntensity={marker.isSelected || marker.isHovered ? 0.6 : 0.3}
                roughness={0.4}
              />
            </mesh>
          )
      )}
    </group>
  )
}

function Scene({ countries, onCountrySelect, selectedCountry }: GlobeProps) {
  return (
    <>
      <ambientLight intensity={0.8} />
      <directionalLight position={[5, 3, 5]} intensity={1.5} color="#ffffff" />
      <directionalLight position={[-3, -2, -3]} intensity={0.4} color="#6eb5ff" />
      <pointLight position={[0, 0, 4]} intensity={0.6} color="#ffffff" />

      <GlobeMesh
        countries={countries}
        onCountrySelect={onCountrySelect}
        selectedCountry={selectedCountry}
      />

      <OrbitControls
        enableZoom={true}
        enablePan={false}
        minDistance={1.8}
        maxDistance={4}
        rotateSpeed={0.4}
        zoomSpeed={0.6}
        autoRotate={false}
      />
    </>
  )
}

export default function Globe({ countries, onCountrySelect, selectedCountry }: GlobeProps) {
  return (
    <div className="h-full min-h-[500px] w-full" style={{ backgroundColor: '#FAFAF9' }}>
      <Canvas
        camera={{ position: [0, 0, 2.8], fov: 42 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <Scene
          countries={countries}
          onCountrySelect={onCountrySelect}
          selectedCountry={selectedCountry}
        />
      </Canvas>
    </div>
  )
}
