"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
} from "react";
import { Toast, type ToastType } from "@/components/ui/Toast";

type ToastItem = {
  id: string;
  message: string;
  type: ToastType;
};

type ToastContextType = {
  toast: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
};

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const remove = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback((message: string, type: ToastType = "info") => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setItems((prev) => [...prev, { id, message, type }]);
  }, []);

  const success = useCallback((message: string) => toast(message, "success"), [toast]);
  const error = useCallback((message: string) => toast(message, "error"), [toast]);
  const info = useCallback((message: string) => toast(message, "info"), [toast]);

  return (
    <ToastContext.Provider value={{ toast, success, error, info }}>
      {children}
      <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2">
        {items.map((t) => (
          <Toast
            key={t.id}
            message={t.message}
            type={t.type}
            onDismiss={() => remove(t.id)}
            duration={4000}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) return {
    toast: () => {},
    success: () => {},
    error: () => {},
    info: () => {},
  };
  return ctx;
}
