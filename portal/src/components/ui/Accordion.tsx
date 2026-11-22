"use client";

import React, { useState } from "react";
import clsx from "clsx";

export interface AccordionItemProps {
  id: string;
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  id,
  title,
  children,
  defaultOpen = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const buttonId = `accordion-btn-${id}`;
  const panelId = `accordion-panel-${id}`;

  return (
    <div className="border border-[#CBD2DC] rounded-lg bg-white overflow-hidden mb-3 shadow-xs">
      <h3>
        <button
          id={buttonId}
          type="button"
          aria-expanded={isOpen}
          aria-controls={panelId}
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center justify-between p-4 text-left font-bold text-sm md:text-base text-[#101828] hover:bg-[#F8FAFC] transition-colors cursor-pointer min-h-[48px]"
        >
          <span>{title}</span>
          <svg
            className={clsx(
              "w-5 h-5 text-[#1351B4] transition-transform duration-200 shrink-0 ml-2",
              isOpen ? "rotate-180" : "rotate-0"
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </h3>

      <div
        id={panelId}
        role="region"
        aria-labelledby={buttonId}
        hidden={!isOpen}
        className="px-4 pb-4 pt-1 text-sm text-[#4A5568] leading-relaxed border-t border-[#F1F3F6]"
      >
        {children}
      </div>
    </div>
  );
};

