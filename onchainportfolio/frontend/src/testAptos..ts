import { Aptos, AptosConfig, Network } from "@aptos-labs/ts-sdk";

const config = new AptosConfig({ network: Network.TESTNET });
const aptos = new Aptos(config);

async function main() {
  const address = "0xe037e246dfd66661c6162e0dff968d64753eea38af08b1da2695e8464dbfce6a";
  const balance = await aptos.getAccountAPTAmount({ accountAddress: address });
  console.log("APT balance:", Number(balance) / 1e8, "APT");
}
main().catch(console.error);
