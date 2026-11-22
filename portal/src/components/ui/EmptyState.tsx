import React from "react";
import clsx from "clsx";
import { Button } from "./Button";

export interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "Nenhum serviço encontrado. Tente outro termo ou categoria.", // MSG-01 literal
  description = "Confira a grafia, remova filtros ou explore uma das categorias sugeridas abaixo.",
  actionLabel,
  onAction,
  className,
}) => {
  return (
    <div
      className={clsx(
        "flex flex-col items-center justify-center p-8 md:p-12 text-center bg-white rounded-lg border border-[#CBD2DC] my-4 shadow-sm",
        className
      )}
    >
      <div className="w-14 h-14 rounded-full bg-[#EFF5FF] text-[#1351B4] flex items-center justify-center mb-4" aria-hidden="true">
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <h3 className="text-base md:text-lg font-bold text-[#101828] max-w-md mb-2">
        {title}
      </h3>

      <p className="text-sm text-[#4A5568] max-w-md mb-6 leading-relaxed">
        {description}
      </p>

      {actionLabel && onAction && (
        <Button variant="secondary" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
};

