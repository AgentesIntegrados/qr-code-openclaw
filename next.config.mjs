/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_EVOLUTION_URL: process.env.NEXT_PUBLIC_EVOLUTION_URL,
    NEXT_PUBLIC_EVOLUTION_API: process.env.NEXT_PUBLIC_EVOLUTION_API,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL
  },
  images: {
    domains: ['localhost'],
  },
  eslint: {
    ignoreDuringBuilds: true
  },
  typescript: {
    ignoreBuildErrors: true
  }
};
const nextConfig = {};

export default nextConfig;
