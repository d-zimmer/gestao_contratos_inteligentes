require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.27",  // Versão do Solidity que você está usando
  networks: {
    sepolia: {
      url: "https://rpc.sepolia.org",  // URL da rede de teste Sepolia
      accounts: [`0x${YOUR_PRIVATE_KEY}`]  // Substitua YOUR_PRIVATE_KEY pela sua chave privada MetaMask
    }
  }
};
