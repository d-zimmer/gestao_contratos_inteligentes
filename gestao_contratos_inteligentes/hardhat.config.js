require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.27",  // Versão do Solidity que você está usando
  networks: {
    sepolia: {
      url: "https://rpc.sepolia.org",  // URL da rede de teste Sepolia
      accounts: [`8ff67494a5678a8532b9a9b3d7e20854fa65f0024558a9e7cbb9d16e1146712d`]  // Substitua YOUR_PRIVATE_KEY pela sua chave privada MetaMask
    }
  }
};
