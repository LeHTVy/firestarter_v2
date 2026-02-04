import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  allowedDevOrigins: ["192.168.1.95", "localhost:3000"],
  experimental: {}
};

export default nextConfig;
