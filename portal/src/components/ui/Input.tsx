import React from "react";
import clsx from "clsx";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
  isRequired?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, helperText, isRequired = false, id, ...props }, ref) => {
    const inputId = id || React.useId();
    const errorId = `${inputId}-error`;
    const helperId = `${inputId}-helper`;

    return (
      <div className="w-full flex flex-col gap-1.5 text-left">
        <label htmlFor={inputId} className="text-sm font-semibold text-[#101828] flex items-center gap-1">
          {label}
          {isRequired && <span className="text-[#E52207]" aria-hidden="true">*</span>}
        </label>

        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={clsx(error && errorId, helperText && helperId)}
          className={clsx(
            "w-full rounded-md border px-3.5 py-2.5 text-sm text-[#101828] placeholder-[#667085] bg-white transition-colors min-h-[44px]",
            "focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[#1351B4]",
            error
              ? "border-[#E52207] focus-visible:outline-[#E52207]"
              : "border-[#CBD2DC] hover:border-[#4A5568]",
            "disabled:bg-[#F1F3F6] disabled:text-[#667085] disabled:cursor-not-allowed",
            className
          )}
          {...props}
        />

        {error && (
          <span id={errorId} className="text-xs font-medium text-[#E52207] flex items-center gap-1" role="alert">
            <svg className="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
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

Input.displayName = "Input";

