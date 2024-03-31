import "@nomiclabs/hardhat-etherscan";
import "@nomiclabs/hardhat-truffle5";
import "@nomiclabs/hardhat-waffle";
import "@nomiclabs/hardhat-web3";
import "@openzeppelin/hardhat-upgrades";
import "@typechain/hardhat";
import * as dotenv from "dotenv";
import "hardhat-gas-reporter";
import { HardhatUserConfig } from "hardhat/config";
import "solidity-coverage";
import "tsconfig-paths";

dotenv.config();

const config: HardhatUserConfig = {
  solidity: {
    compilers: [
      {
        version: "0.8.2",
        settings: {
          optimizer: {
            enabled: true,
            runs: 150,
          },
        },
      },
    ],
  },
  networks: {
    mumbai: {
      url: "https://polygon-mumbai-bor-rpc.publicnode.com	",
      chainId: 80001,
      accounts:
        process.env.PRIVATE_KEY !== undefined ? [process.env.PRIVATE_KEY] : [],
    },
    bsc: {
      url: "https://goerli.infura.io/v3/dea2c8c95a674dab87bbd16f7921caf2",
      chainId: 5,
      accounts:
        process.env.PRIVATE_KEY !== undefined ? [process.env.PRIVATE_KEY] : [],
    },
    bscTestnet: {
      url: "https://data-seed-prebsc-1-s1.binance.org:8545/",
      gas: 2000000,
      chainId: 97,
      accounts:
        process.env.PRIVATE_KEY !== undefined ? [process.env.PRIVATE_KEY] : [],
    },
    bscFork: {
      url: "http://127.0.0.1:8545/",
    },
    ethereum: {
      url: "https://mainnet.infura.io/v3/fffda8246d9241f2aa056b563090838d",
      chainId: 1,
      accounts:
        process.env.PRIVATE_KEY_MAINNET !== undefined
          ? [process.env.PRIVATE_KEY_MAINNET]
          : [],
    },
    polygon: {
      url: "http://127.0.0.1:8545/",
      gas: 2000000,
      chainId: 1337,
      accounts:
        process.env.PRIVATE_KEY_MAINNET !== undefined
          ? [process.env.PRIVATE_KEY_MAINNET]
          : [],
    },
  },
  etherscan: {
    // apiKey: {
    //   bsc: process.env.BSC_API_KEY_PROD ? process.env.BSC_API_KEY_PROD : "",
    //   bscTestnet: process.env.BSC_API_KEY ? process.env.BSC_API_KEY : "",
    //   ethereum: process.env.BSC_API_KEY ? process.env.BSC_API_KEY : "",
    // },
    apiKey: "TPDKYSM7FGPD28VCPW3IK3T43N61JZR66T",
  },
  gasReporter: {
    enabled: false,
    currency: "USD",
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  mocha: {
    timeout: 50000,
  },
};

export default config;
