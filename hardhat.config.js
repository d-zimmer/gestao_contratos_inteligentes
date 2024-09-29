require('dotenv').config();
require("@nomicfoundation/hardhat-toolbox");

const privateKey = process.env.PRIVATE_KEY;

module.exports = {
  solidity: "0.8.27",
  networks: {
    localhost: {  // Rede local do Hardhat
      url: "http://127.0.0.1:8545",
      accounts: [privateKey]  // Usar a chave privada configurada no .env
    }
  }
};
