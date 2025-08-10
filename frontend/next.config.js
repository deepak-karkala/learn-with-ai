/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // Keep type checking during builds
    ignoreBuildErrors: false,
  },
  eslint: {
    // Skip ESLint during production builds to avoid devDeps issues on CI
    ignoreDuringBuilds: true,
  },
}

module.exports = nextConfig