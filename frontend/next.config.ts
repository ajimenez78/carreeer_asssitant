import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  devIndicators: false,
  distDir: process.env.CAREER_NEXT_DIST_DIR || ".next",
};

export default nextConfig;
