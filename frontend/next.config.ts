import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@vapi-ai/web"],
  turbopack: {},
};

export default nextConfig;
