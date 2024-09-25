require('dotenv').config();
require("@nomicfoundation/hardhat-toolbox");

const privateKey = process.env.PRIVATE_KEY;

module.exports = {
  solidity: "0.8.27",  // Versão do Solidity que você está usando
  networks: {
    sepolia: {
      url: "https://rpc.sepolia.org",  // URL da rede de teste Sepolia
      accounts: [privateKey]  // Substitua YOUR_PRIVATE_KEY pela sua chave privada MetaMask
    }
  }
};
