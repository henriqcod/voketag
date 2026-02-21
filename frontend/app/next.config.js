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

  // LOW ENHANCEMENT: Optimize imports at package level
  experimental: {
    optimizePackageImports: [
      "@mui/material",
      "@ui/components",
      "lodash",
      "lodash-es",
      "react-icons",
    ],
  },

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

    // Production optimizations
    if (process.env.NODE_ENV === "production") {
      // Tree shaking for better bundle size
      config.optimization = {
        ...config.optimization,
        usedExports: true,
        sideEffects: false,
        // LOW ENHANCEMENT: Code splitting strategy
        splitChunks: {
          chunks: "all",
          cacheGroups: {
            // Separate vendor code from app code
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: "vendors",
              priority: 10,
              reuseExistingChunk: true,
            },
            // Common chunks used across pages
            common: {
              minChunks: 2,
              priority: 5,
              reuseExistingChunk: true,
            },
          },
        },
      };
    }

    // Bundle analyzer (enable with ANALYZE=true)
    // Usage: ANALYZE=true npm run build
    if (process.env.ANALYZE === "true") {
      const { BundleAnalyzerPlugin } = require("webpack-bundle-analyzer");
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: "static",
          reportFilename: isServer
            ? "../analyze/server.html"
            : "./analyze/client.html",
          openAnalyzer: false,
          // Generate stats.json for programmatic analysis
          generateStatsFile: true,
          statsFilename: isServer
            ? "../analyze/server-stats.json"
            : "./analyze/client-stats.json",
        })
      );
    }

    return config;
  },
};

module.exports = withPWA(nextConfig);
