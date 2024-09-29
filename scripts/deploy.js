async function main() {
  const [deployer] = await ethers.getSigners();

  console.log("Deploying contracts with the account:", deployer.address);

  const RentalAgreement = await ethers.getContractFactory("RentalAgreement");
  const rentalAgreement = await RentalAgreement.deploy(1000, 500);  // Exemplo de parâmetros

  await rentalAgreement.deployed();
  console.log("Contract deployed to:", rentalAgreement.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
