import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  experimental: { tsconfigPaths: true },
  outputFileTracingRoot: path.join(__dirname, ".."),
};

export default nextConfig;
