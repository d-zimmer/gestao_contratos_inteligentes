async function main() {
    const RentalAgreement = await ethers.getContractFactory("RentalAgreement");
    const rental = await RentalAgreement.deploy(1000, 2000);
    await rental.deployed();
    console.log("RentalAgreement deployed to:", rental.address);
  }
  
  main()
    .then(() => process.exit(0))
    .catch(error => {
      console.error(error);
      process.exit(1);
    });
  