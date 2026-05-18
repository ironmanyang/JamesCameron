module.exports = {
  outputDir: 'dist',
  publicPath: '/',
  devServer: {
    port: 8080,
    open: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  lintOnSave: false
}