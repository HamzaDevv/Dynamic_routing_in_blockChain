import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("PCERRoutingModule", (m) => {
  const pcer = m.contract("PCERRouting", []);
  return { pcer };
});
