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
    // In development, proxy API calls to local FastAPI backend
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ]
    }
    return []
  },
}

module.exports = nextConfig