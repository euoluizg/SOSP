import React from "react";
import clsx from "clsx";

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  className?: string;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  className,
}) => {
  if (totalPages <= 1) return null;

  return (
    <nav
      role="navigation"
      aria-label="Paginação de resultados"
      className={clsx("flex items-center justify-center gap-2 mt-8", className)}
    >
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        aria-label="Ir para página anterior"
        className="px-3.5 py-2 text-sm font-semibold text-[#1351B4] rounded-md border border-[#CBD2DC] bg-white hover:bg-[#EFF5FF] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer min-h-[44px]"
      >
        ← Anterior
      </button>

      {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
        const isCurrent = page === currentPage;
        return (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            aria-current={isCurrent ? "page" : undefined}
            aria-label={`Página ${page}`}
            className={clsx(
              "w-11 h-11 text-sm font-bold rounded-md flex items-center justify-center transition-colors cursor-pointer",
              isCurrent
                ? "bg-[#1351B4] text-white shadow-sm"
                : "text-[#101828] border border-[#CBD2DC] bg-white hover:bg-[#EFF5FF]"
            )}
          >
            {page}
          </button>
        );
      })}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        aria-label="Ir para próxima página"
        className="px-3.5 py-2 text-sm font-semibold text-[#1351B4] rounded-md border border-[#CBD2DC] bg-white hover:bg-[#EFF5FF] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer min-h-[44px]"
      >
        Próxima →
      </button>
    </nav>
  );
};

