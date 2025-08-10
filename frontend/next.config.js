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
}

module.exports = nextConfig