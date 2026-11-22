"use client";

import React, { useEffect, useRef } from "react";
import clsx from "clsx";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: "sm" | "md" | "lg";
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "md",
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      document.body.style.overflow = "hidden";

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          onClose();
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => {
        window.removeEventListener("keydown", handleKeyDown);
        document.body.style.overflow = "unset";
        previousActiveElement.current?.focus();
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: "max-w-md",
    md: "max-w-lg",
    lg: "max-w-2xl",
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div
        ref={modalRef}
        className={clsx(
          "w-full bg-white rounded-lg shadow-xl border border-[#CBD2DC] overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-200",
          sizeClasses[size]
        )}
      >
        {/* Header do Modal */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#F1F3F6]">
          <h2 id="modal-title" className="text-lg font-bold text-[#101828]">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="text-[#667085] hover:text-[#101828] p-1.5 rounded-md hover:bg-[#F1F3F6] transition-colors cursor-pointer min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Fechar janela"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Corpo */}
        <div className="px-6 py-5 overflow-y-auto text-sm text-[#4A5568] leading-relaxed">
          {children}
        </div>

        {/* Rodapé opcional */}
        {footer && (
          <div className="px-6 py-4 border-t border-[#F1F3F6] bg-[#F8FAFC] flex justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

