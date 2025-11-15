// src/utils.ts
export const shortenAddress = (addr: string) => {
  if (!addr) return "";
  return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
};

export const formatUSD = (num: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num);

export const formatAmount = (num: number, decimals = 4) =>
  num.toLocaleString("en-US", { maximumFractionDigits: decimals });
