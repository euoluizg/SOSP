import React from "react";
import clsx from "clsx";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "card" | "avatar" | "button";
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, variant = "text", ...props }) => {
  const variantStyles = {
    text: "h-4 w-full rounded",
    card: "h-48 w-full rounded-lg",
    avatar: "h-10 w-10 rounded-full",
    button: "h-11 w-32 rounded-md",
  };

  return (
    <div
      aria-busy="true"
      className={clsx(
        "animate-pulse bg-[#CBD2DC]/40",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
};

