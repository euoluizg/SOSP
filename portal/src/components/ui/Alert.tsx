import React from "react";
import clsx from "clsx";

export interface AlertProps {
  variant?: "info" | "success" | "warning" | "danger";
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  variant = "info",
  title,
  children,
  className,
}) => {
  const styles = {
    info: "bg-[#EFF5FF] border-[#1351B4] text-[#0C326F]",
    success: "bg-[#EAF7ED] border-[#168821] text-[#0E5815]",
    warning: "bg-[#FFF9E6] border-[#FFCD07] text-[#8A6D00]",
    danger: "bg-[#FDECE9] border-[#E52207] text-[#8F1504]",
  };

  return (
    <div
      role="alert"
      className={clsx(
        "p-4 rounded-lg border-l-4 text-sm leading-relaxed shadow-xs my-3",
        styles[variant],
        className
      )}
    >
      {title && <h4 className="font-bold mb-1">{title}</h4>}
      <div>{children}</div>
    </div>
  );
};

