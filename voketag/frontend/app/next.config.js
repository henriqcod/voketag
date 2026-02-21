/** @type {import('next').NextConfig} */
const withPWA = require("@ducanh2912/next-pwa").default({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  fallbacks: { document: "/~offline" },
  extendDefaultRuntimeCaching: true,
  workboxOptions: {
    runtimeCaching: [
      {
        urlPattern: /^https?:\/\/localhost:\d+\/v1\/scan\/.+/,
        handler: "NetworkOnly",
      },
      {
        urlPattern: /^https:\/\/api\.voketag\.com\/.+/,
        handler: "NetworkOnly",
      },
    ],
  },
});

const nextConfig = {
  reactStrictMode: true,
  
  // Security headers
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(self), microphone=(), geolocation=(self), interest-cohort=()",
          },
        ],
      },
    ];
  },

  // Disable X-Powered-By header
  poweredByHeader: false,

  // Enable SWC minification
  swcMinify: true,

  // Compiler options
  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === "production" ? { exclude: ["error", "warn"] } : false,
  },

  // Image optimization
  images: {
    domains: ["voketag.com.br", "cdn.voketag.com.br"],
    formats: ["image/avif", "image/webp"],
  },

  // Webpack optimizations
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Don't bundle these on client
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }

    // LOW FIX: Enable bundle optimization
    // Production optimizations
    if (process.env.NODE_ENV === "production") {
      // Tree shaking for better bundle size
      config.optimization = {
        ...config.optimization,
        usedExports: true,
        sideEffects: false,
      };
    }

    // Bundle analyzer (enable with ANALYZE=true)
    if (process.env.ANALYZE === "true") {
      const { BundleAnalyzerPlugin } = require("webpack-bundle-analyzer");
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: "static",
          reportFilename: isServer
            ? "../analyze/server.html"
            : "./analyze/client.html",
          openAnalyzer: false,
        })
      );
    }

    return config;
  },
};

module.exports = withPWA(nextConfig);
