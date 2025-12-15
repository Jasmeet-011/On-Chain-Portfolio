// src/components/Logo.tsx - FIXED: Theme-aware text color
import React from "react";

interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  iconOnly?: boolean;
  theme?: "dark" | "light";
  className?: string;
}

const sizeConfig = {
  sm: { fontSize: "text-base", iconSize: "w-6 h-6", iconText: "text-xs" },
  md: { fontSize: "text-xl", iconSize: "w-8 h-8", iconText: "text-sm" },
  lg: { fontSize: "text-2xl", iconSize: "w-10 h-10", iconText: "text-base" },
  xl: { fontSize: "text-3xl", iconSize: "w-12 h-12", iconText: "text-lg" },
};

const Logo: React.FC<LogoProps> = ({
  size = "md",
  iconOnly = false,
  theme = "dark",
  className = "",
}) => {
  const config = sizeConfig[size];
  
  // ✅ FIXED: Text color changes based on theme
  const textColor = theme === "dark" ? "text-white" : "text-slate-900";

  if (iconOnly) {
    return (
      <div className={`inline-flex items-center ${className}`}>
        <div className={`${config.iconSize} bg-blue-600 rounded-lg flex items-center justify-center`}>
          <span className={`text-white font-bold ${config.iconText}`}>C</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      {/* Icon - always blue background with white text */}
      <div className={`${config.iconSize} bg-blue-600 rounded-lg flex items-center justify-center`}>
        <span className={`text-white font-bold ${config.iconText}`}>C</span>
      </div>
      
      {/* Text - changes color based on theme */}
      <span className={`font-bold ${config.fontSize} ${textColor}`}>
        Chain<span className="text-blue-500">IQ</span>
      </span>
    </div>
  );
};

export default Logo;