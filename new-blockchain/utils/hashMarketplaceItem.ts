/* eslint-disable node/no-unsupported-features/es-syntax */
// eslint-disable-next-line node/no-unpublished-import
import hre from "hardhat";

const SIGNING_DOMAIN_NAME = "Marketplace-Item";
const SIGNING_DOMAIN_VERSION = "1";

export const hashOrderItem = async (types: any, auth: any, orderItem: any) => {
  const domain = {
    name: SIGNING_DOMAIN_NAME,
    version: SIGNING_DOMAIN_VERSION,
    verifyingContract: auth.contract,
    chainId: hre.network.config.chainId,
  };

  const signature = await auth.signer._signTypedData(domain, types, orderItem);

  return {
    ...orderItem,
    signature,
  };
};
