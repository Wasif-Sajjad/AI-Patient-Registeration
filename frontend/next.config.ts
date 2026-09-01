import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@vapi-ai/web"],
  turbopack: {},
};

export default nextConfig;
