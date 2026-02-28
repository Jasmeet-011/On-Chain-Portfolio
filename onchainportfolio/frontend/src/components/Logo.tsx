// src/components/Logo.tsx - PROFESSIONAL: White/Black Icon
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
  
  // Text color based on theme
  const textColor = theme === "dark" ? "text-white" : "text-gray-900";
  
  // ✅ NEW: Icon inverts based on theme (white in dark, black in light)
  const iconBg = theme === "dark" ? "bg-white" : "bg-black";
  const iconText = theme === "dark" ? "text-black" : "text-white";

  if (iconOnly) {
    return (
      <div className={`inline-flex items-center ${className}`}>
        <div className={`${config.iconSize} ${iconBg} rounded-lg flex items-center justify-center`}>
          <span className={`${iconText} font-bold ${config.iconText}`}>C</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      {/* ✅ Icon - white background in dark mode, black in light mode */}
      <div className={`${config.iconSize} ${iconBg} rounded-lg flex items-center justify-center`}>
        <span className={`${iconText} font-bold ${config.iconText}`}>C</span>
      </div>
      
      <span className={`font-bold ${config.fontSize} ${textColor}`}>
        Chain<span className={theme === "dark" ? "text-white" : "text-gray-900"}>Lens</span>
      </span>
    </div>
  );
};

export default Logo;