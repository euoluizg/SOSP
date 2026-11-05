import React from "react";
import clsx from "clsx";
import { ServiceChannel } from "@/types/api";

export interface TagProps {
  label?: string;
  children?: React.ReactNode;
  variant?: "neutral" | "channel" | "success" | "warning" | "danger" | "info";
  channel?: ServiceChannel;
  className?: string;
}

export const Tag: React.FC<TagProps> = ({ label, children, variant = "neutral", channel, className }) => {
  let style = "bg-[#F1F3F6] text-[#4A5568] border-[#CBD2DC]";
  let dotColor = "#4A5568";

  const content = children || label;

  if (channel === "online") {
    style = "bg-[#EFF5FF] text-[#1351B4] border-[#1351B4]/20";
    dotColor = "#1351B4";
  } else if (channel === "inPerson") {
    style = "bg-[#FFF9E6] text-[#8A6D00] border-[#FFCD07]/40";
    dotColor = "#8A6D00";
  } else if (channel === "hybrid") {
    style = "bg-[#EFF5FF] text-[#0C326F] border-[#1351B4]/30";
    dotColor = "#1351B4";
  } else if (variant === "success") {
    style = "bg-[#EAF7ED] text-[#168821] border-[#168821]/30";
    dotColor = "#168821";
  } else if (variant === "danger") {
    style = "bg-[#FDECE9] text-[#E52207] border-[#E52207]/30";
    dotColor = "#E52207";
  } else if (variant === "warning") {
    style = "bg-[#FFF9E6] text-[#8A6D00] border-[#FFCD07]/40";
    dotColor = "#8A6D00";
  }

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border",
        style,
        className
      )}
    >
      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: dotColor }} aria-hidden="true" />
      {content}
    </span>
  );
};

