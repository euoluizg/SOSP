import React from "react";
import clsx from "clsx";

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: SelectOption[];
  error?: string;
  helperText?: string;
  isRequired?: boolean;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, options, error, helperText, isRequired = false, id, ...props }, ref) => {
    const selectId = id || React.useId();
    const errorId = `${selectId}-error`;
    const helperId = `${selectId}-helper`;

    return (
      <div className="w-full flex flex-col gap-1.5 text-left">
        <label htmlFor={selectId} className="text-sm font-semibold text-[#101828] flex items-center gap-1">
          {label}
          {isRequired && <span className="text-[#E52207]" aria-hidden="true">*</span>}
        </label>

        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            aria-invalid={!!error}
            aria-describedby={clsx(error && errorId, helperText && helperId)}
            className={clsx(
              "w-full rounded-md border px-3.5 py-2.5 text-sm text-[#101828] bg-white transition-colors appearance-none min-h-[44px] pr-10 cursor-pointer",
              "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#1351B4]",
              error
                ? "border-[#E52207] focus-visible:outline-[#E52207]"
                : "border-[#CBD2DC] hover:border-[#4A5568]",
              "disabled:bg-[#F1F3F6] disabled:text-[#667085] disabled:cursor-not-allowed",
              className
            )}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-[#4A5568]">
            <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20" aria-hidden="true">
              <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
            </svg>
          </div>
        </div>

        {error && (
          <span id={errorId} className="text-xs font-medium text-[#E52207] flex items-center gap-1" role="alert">
            {error}
          </span>
        )}

        {!error && helperText && (
          <span id={helperId} className="text-xs text-[#667085]">
            {helperText}
          </span>
        )}
      </div>
    );
  }
);

Select.displayName = "Select";

