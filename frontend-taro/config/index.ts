import { defineConfig, type UserConfigExport } from "@tarojs/cli";
import path from "path";

const config: UserConfigExport = {
  projectName: "xianxia-agent",
  date: "2026-07-08",
  designWidth: 750,
  deviceRatio: {
    640: 2.34 / 2,
    750: 1,
    828: 1.81 / 2
  },
  sourceRoot: "src",
  outputRoot: "dist",
  alias: {
    "@": path.resolve(__dirname, "..", "src")
  },
  framework: "react",
  compiler: {
    type: "webpack5",
    prebundle: {
      enable: false
    }
  },
  cache: {
    enable: false
  },
  mini: {
    postcss: {
      pxtransform: {
        enable: true,
        config: {}
      },
      cssModules: {
        enable: false
      }
    }
  },
  h5: {
    publicPath: "/",
    staticDirectory: "static",
    devServer: {
      host: "127.0.0.1",
      port: 10086,
      static: false,
      historyApiFallback: true
    },
    output: {
      filename: "js/[name].[hash:8].js",
      chunkFilename: "js/[name].[chunkhash:8].js"
    },
    htmlPluginOption: {
      template: path.resolve(__dirname, "..", "src", "index.html")
    },
    miniCssExtractPluginOption: {
      ignoreOrder: true,
      filename: "css/[name].[hash].css",
      chunkFilename: "css/[name].[chunkhash].css"
    },
    postcss: {
      autoprefixer: {
        enable: true
      },
      cssModules: {
        enable: false
      }
    }
  }
};

export default defineConfig(async () => config);
