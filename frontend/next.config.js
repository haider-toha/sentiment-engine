/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['three'],
  // Static export for Render deployment
  output: 'export',
  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig

