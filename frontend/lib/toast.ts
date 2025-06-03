import { toast } from "sonner"

// Success toast
export function showSuccess(title: string, description?: string) {
  toast.success(title, {
    description,
    duration: 3000,
  })
}

// Error toast
export function showError(title: string, description?: string) {
  toast.error(title, {
    description,
    duration: 4000,
  })
}

// Info toast
export function showInfo(title: string, description?: string) {
  toast.info(title, {
    description,
    duration: 3000,
  })
}

// Warning toast
export function showWarning(title: string, description?: string) {
  toast.warning(title, {
    description,
    duration: 3500,
  })
}
