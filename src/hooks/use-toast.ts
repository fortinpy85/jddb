// shadcn/ui compatible useToast hook
import {
  useToast as useToastOriginal,
  Toast as ToastOriginal,
} from "@/components/ui/toast";

interface ToastOptions {
  title: string;
  description?: string;
  variant?: "default" | "destructive";
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function useToast() {
  const { addToast, updateToast, removeToast, toasts } = useToastOriginal();

  const toast = (options: ToastOptions) => {
    const type = options.variant === "destructive" ? "error" : "info";
    addToast({
      title: options.title,
      description: options.description,
      type,
      duration: options.duration,
      action: options.action,
    });
  };

  return {
    toast,
    toasts,
    updateToast,
    removeToast,
  };
}

export type { ToastOptions as Toast };
