import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
  typescript: {
    tsconfigPath: "tsconfig.json",
  },
};

export default nextConfig;
