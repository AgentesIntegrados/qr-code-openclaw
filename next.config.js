/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  publicRuntimeConfig: {
    NEXT_PUBLIC_EVOLUTION_URL: process.env.NEXT_PUBLIC_EVOLUTION_URL,
    NEXT_PUBLIC_EVOLUTION_API: process.env.NEXT_PUBLIC_EVOLUTION_API,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL
  },
  output: 'standalone',
  reactStrictMode: true,
  webpack: (config, { dev, isServer }) => {
    if (!dev && !isServer) {
      Object.assign(config.resolve.alias, {
        'react-devtools-core': false,
      });
    }
    return config;
  },
  async rewrites() {
    return [
      {
        source: '/uploads/:path*',
        destination: '/api/uploads/:path*',
      },
    ]
  }
}

module.exports = nextConfig
