/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_ADMIN_API || "http://127.0.0.1:8082";
    return [{ source: "/api/admin/:path*", destination: `${api}/:path*` }];
  },
};
module.exports = nextConfig;
