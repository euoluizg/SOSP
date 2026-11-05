"use client";

import React, { useState, useEffect } from "react";
import { Clock, RefreshCw, LogIn } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface SessionTimeoutModalProps {
  isOpen: boolean;
  onExtendSession: () => void;
  onLogout: () => void;
  remainingSeconds?: number;
}

export const SessionTimeoutModal: React.FC<SessionTimeoutModalProps> = ({
  isOpen,
  onExtendSession,
  onLogout,
  remainingSeconds = 120, // 2 minutos para timeout
}) => {
  const [seconds, setSeconds] = useState(remainingSeconds);

  useEffect(() => {
    if (!isOpen) {
      setSeconds(remainingSeconds);
      return;
    }

    const timer = setInterval(() => {
      setSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          onLogout();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isOpen, remainingSeconds, onLogout]);

  if (!isOpen) return null;

  const minutes = Math.floor(seconds / 60);
  const formattedSeconds = String(seconds % 60).padStart(2, "0");

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="session-timeout-title"
      aria-describedby="session-timeout-desc"
    >
      <div className="w-full max-w-md bg-white rounded-xl shadow-2xl border border-amber-200 p-6 text-center">
        <div className="mx-auto w-14 h-14 bg-amber-100 rounded-full flex items-center justify-center text-amber-600 mb-4">
          <Clock className="w-8 h-8" />
        </div>

        <h2 id="session-timeout-title" className="text-xl font-bold text-gray-900">
          Sua sessão está prestes a expirar
        </h2>

        <p id="session-timeout-desc" className="mt-2 text-sm text-gray-600">
          Por motivos de segurança (regra RN-28), após 30 minutos de inatividade sua sessão é
          automaticamente encerrada.
        </p>

        <div className="my-6 p-4 bg-amber-50 rounded-lg border border-amber-200">
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-800">
            Tempo restante para desconexão
          </span>
          <div className="text-3xl font-mono font-bold text-amber-900 mt-1">
            {minutes}:{formattedSeconds}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button variant="secondary" onClick={onLogout} className="flex-1">
            <LogIn className="w-4 h-4 mr-2" />
            Sair agora
          </Button>
          <Button variant="primary" onClick={onExtendSession} className="flex-1">
            <RefreshCw className="w-4 h-4 mr-2" />
            Continuar conectado
          </Button>
        </div>
      </div>
    </div>
  );
};

