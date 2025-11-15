import React from "react";
import { useAppContext } from "../context/AppContext";
import { formatAmount } from "../utils";

interface Props {
  positions: any[];
}

const PositionsTable: React.FC<Props> = ({ positions }) => {
  const { theme } = useAppContext();

  if (!positions || positions.length === 0) return null;

  return (
    <div className="overflow-x-auto mt-4">
      <table className="min-w-full">
        <thead>
          <tr
            className={`border-b ${
              theme === "dark" ? "border-gray-700" : "border-gray-200"
            }`}
          >
            <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Protocol</th>
            <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Type</th>
            <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Asset</th>
            <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Amount</th>
            <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>APY</th>
          </tr>
        </thead>
        <tbody>
          {positions.map((pos, i) => (
            <tr
              key={i}
              className={`border-b transition-colors ${
                theme === "dark"
                  ? "border-gray-800 hover:bg-gray-800/50"
                  : "border-gray-100 hover:bg-gray-50"
              }`}
            >
              <td
                className={`px-4 py-4 font-medium ${
                  theme === "dark" ? "text-gray-200" : "text-gray-900"
                }`}
              >
                {pos.protocol}
              </td>
              <td className="px-4 py-4">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    pos.position_type === "supply"
                      ? "bg-green-500/10 text-green-400 border border-green-500/20"
                      : "bg-orange-500/10 text-orange-400 border border-orange-500/20"
                  }`}
                >
                  {pos.position_type}
                </span>
              </td>
              <td
                className={`px-4 py-4 font-semibold ${
                  theme === "dark" ? "text-gray-300" : "text-gray-700"
                }`}
              >
                {pos.symbol}
              </td>
              <td
                className={`px-4 py-4 text-right font-medium ${
                  theme === "dark" ? "text-gray-300" : "text-gray-700"
                }`}
              >
                {formatAmount(pos.supplied)}
              </td>
              <td className="px-4 py-4 text-right font-semibold text-green-400">
                {pos.apy}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PositionsTable;
