import type { NextConfig } from "next";
import path from "path";
import { PHASE_PRODUCTION_BUILD } from "next/constants";
import { assertValidBuildEnv } from "./src/utils/buildEnvGuard";

export default function config(phase: string): NextConfig {
  if (phase === PHASE_PRODUCTION_BUILD) {
    assertValidBuildEnv();
  }

  return {
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
}

