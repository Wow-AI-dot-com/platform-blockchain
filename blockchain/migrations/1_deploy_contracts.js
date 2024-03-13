const ResourceRegistration = artifacts.require("ResourceRegistration");
module.exports = function(deployer) {
    deployer.deploy(ResourceRegistration);
};