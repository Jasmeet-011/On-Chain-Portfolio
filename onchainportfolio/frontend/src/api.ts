// src/api.ts
export const MOCK_MODE = true;

const MOCK_RESPONSE = {
  text: "You hold 12.345 APT and 150.00 USDC. You also have 2 NFTs in your wallet.",
  data: {
    balances: [
      {
        symbol: "APT",
        token_address: "0x1::aptos_coin::AptosCoin",
        raw_amount: "1234500000",
        decimals: 8,
        display_amount: 12.345,
      },
      {
        symbol: "USDC",
        token_address:
          "0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa",
        raw_amount: "150000000",
        decimals: 6,
        display_amount: 150.0,
      },
    ],
    prices: { APT: 7.12, USDC: 1.0 },
    nfts: [
      {
        collection: "Aptos Monkeys",
        name: "Monkey #42",
        token_id: "42",
        media_url:
          "https://via.placeholder.com/200/FF6B6B/FFFFFF?text=Monkey+42",
      },
      {
        collection: "Digital Cats",
        name: "Cat #7",
        token_id: "7",
        media_url:
          "https://via.placeholder.com/200/4ECDC4/FFFFFF?text=Cat+7",
      },
    ],
    positions: [
      {
        protocol: "Aries Markets",
        position_type: "supply",
        symbol: "USDC",
        supplied: 50.0,
        apy: 3.2,
      },
      {
        protocol: "Thala",
        position_type: "supply",
        symbol: "APT",
        supplied: 5.0,
        apy: 2.8,
      },
    ],
  },
};

export const api = {
  async health() {
    if (MOCK_MODE) return { status: "ok (mock)" };
    const res = await fetch("/api/health");
    return res.json();
  },

  async chat(message: string, wallet?: string) {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return MOCK_RESPONSE;
    }
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, wallet_address: wallet }),
    });
    return res.json();
  },
};
