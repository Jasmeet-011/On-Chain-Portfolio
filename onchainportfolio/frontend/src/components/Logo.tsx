import React from "react";

interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  iconOnly?: boolean;
  theme?: "dark" | "light";
  className?: string;
}

const sizeConfig = {
  sm: { fontSize: "text-base",  iconSize: "w-7 h-7",   iconText: "text-xs"  },
  md: { fontSize: "text-lg",    iconSize: "w-8 h-8",   iconText: "text-sm"  },
  lg: { fontSize: "text-2xl",   iconSize: "w-10 h-10", iconText: "text-base" },
  xl: { fontSize: "text-3xl",   iconSize: "w-12 h-12", iconText: "text-lg"  },
};

const Logo: React.FC<LogoProps> = ({
  size = "md",
  iconOnly = false,
  theme = "dark",
  className = "",
}) => {
  const config = sizeConfig[size];
  const textColor = theme === "dark" ? "text-white" : "text-gray-900";

  return (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      <div
        className={`${config.iconSize} rounded-xl flex items-center justify-center shrink-0 bg-linear-to-br from-blue-500 to-indigo-600`}
        style={{ boxShadow: "0 2px 8px rgba(99,102,241,0.35)" }}
      >
        <span className={`text-white font-bold ${config.iconText} tracking-tight`}>CL</span>
      </div>
      {!iconOnly && (
        <span className={`font-bold ${config.fontSize} ${textColor} tracking-tight`}>
          Chain<span className="text-blue-400">Lens</span>
        </span>
      )}
    </div>
  );
};

export default Logo;
