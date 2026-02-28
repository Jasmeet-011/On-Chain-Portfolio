/**
 * ENS (Ethereum Name Service) utilities
 * Resolves .eth names to addresses and vice-versa using a public Ethereum RPC.
 */
import { createPublicClient, http } from "viem";
import { mainnet } from "viem/chains";
import { normalize } from "viem/ens";

// Public Ethereum mainnet RPC (Cloudflare + LlamaRPC fallbacks)
const RPC_URLS = [
  "https://cloudflare-eth.com",
  "https://eth.llamarpc.com",
  "https://rpc.ankr.com/eth",
];

function makeClient(rpcUrl: string) {
  return createPublicClient({
    chain: mainnet,
    transport: http(rpcUrl, { timeout: 8_000 }),
  });
}

/** Returns true if the string looks like an ENS name (contains a dot, e.g. vitalik.eth) */
export function isENSName(input: string): boolean {
  const trimmed = input.trim().toLowerCase();
  return trimmed.includes(".") && !trimmed.startsWith("0x") && trimmed.length > 3;
}

/**
 * Resolve an ENS name to its EVM address.
 * Tries multiple public RPCs in sequence until one succeeds.
 * Returns null if the name doesn't resolve or an error occurs.
 */
export async function resolveENSName(name: string): Promise<string | null> {
  if (!isENSName(name)) return null;

  let normalized: string;
  try {
    normalized = normalize(name.trim().toLowerCase());
  } catch {
    return null; // invalid ENS name format
  }

  for (const rpc of RPC_URLS) {
    try {
      const client = makeClient(rpc);
      const address = await client.getEnsAddress({ name: normalized });
      if (address) return address;
    } catch {
      // try next RPC
    }
  }
  return null;
}

/**
 * Reverse-lookup: given a 0x EVM address, return its primary ENS name.
 * Returns null if the address has no ENS name or an error occurs.
 */
export async function lookupENSName(address: string): Promise<string | null> {
  if (!address.startsWith("0x") || address.length !== 42) return null;

  for (const rpc of RPC_URLS) {
    try {
      const client = makeClient(rpc);
      const name = await client.getEnsName({ address: address as `0x${string}` });
      if (name) return name;
    } catch {
      // try next RPC
    }
  }
  return null;
}
