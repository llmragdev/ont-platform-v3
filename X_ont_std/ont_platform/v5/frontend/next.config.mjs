/** @type {import('next').NextConfig} */
const nextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/api/:path*",
      },
    ];
  },
  webpack(config, { isServer }) {
    if (!isServer) {
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...config.optimization.splitChunks?.cacheGroups,
          reactVendors: {
            test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
            name: "react-vendors",
            chunks: "all",
            priority: 30,
            reuseExistingChunk: true,
          },
          graphVendors: {
            test: /[\\/]node_modules[\\/](reactflow|cytoscape|cytoscape-dagre|dagre|graphlib)[\\/]/,
            name: "graph-vendors",
            chunks: "all",
            priority: 25,
            reuseExistingChunk: true,
          },
        },
      };
    }
    return config;
  },
};

export default nextConfig;
