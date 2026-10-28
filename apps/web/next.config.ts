import type { NextConfig } from "next";
const apiURL = process.env.SCOS_API_URL || "http://127.0.0.1:8100";
const url = new URL(apiURL);
if (
  url.username ||
  url.password ||
  url.pathname !== "/" ||
  !["http:", "https:"].includes(url.protocol)
) {
  throw new Error(
    "SCOS_API_URL must be an HTTP(S) origin without credentials or a path",
  );
}
if (process.env.VERCEL && url.protocol !== "https:") {
  throw new Error("Hosted frontend requires an HTTPS API origin");
}
const config: NextConfig = {
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: apiURL.replace(/\/$/, "") + "/api/:path*",
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
  devIndicators: false,
};
export default config;
