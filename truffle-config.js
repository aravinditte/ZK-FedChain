module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 7545,
      network_id: "5777"
    }
  },
  compilers: {
    solc: {
      version: "0.8.17",
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        },
        viaIR: true // Use the new IR-based compiler pipeline
      }
    }
  },
  plugins: [],
  mocha: {
    timeout: 100000
  }
};
