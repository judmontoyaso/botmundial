import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://mundialback.juanmontoya.me/api/:path*',
      },
    ];
  },
};

export default nextConfig;
