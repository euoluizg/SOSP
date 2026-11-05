import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  outputFileTracingRoot: path.join(__dirname),
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  async rewrites() {
    return [
      { source: "/busca", destination: "/servicos" },
      { source: "/agendamentos", destination: "/cidadao/meus-agendamentos" },
      { source: "/acompanhar", destination: "/cidadao/meus-agendamentos" },
    ];
  },
};

export default nextConfig;

