/** @type {import('next').NextConfig} */
const path = require('path')

const nextConfig = {
  typescript: {
    // Keep type checking during builds
    ignoreBuildErrors: false,
  },
  eslint: {
    // Skip ESLint during production builds to avoid devDeps issues on CI
    ignoreDuringBuilds: true,
  },
  webpack: (config) => {
    // Ensure Webpack can resolve the @ alias in all environments
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': path.resolve(__dirname),
    }
    return config
  },
  async rewrites() {
    // Determine backend URL based on environment
    let backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig