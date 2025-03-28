import * as React from "react";
import { cn } from "@/lib/utils";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(({ className, ...props }, ref) => {
  return (
    <select ref={ref} className={cn("border p-2 rounded", className)} {...props} />
  );
});
Select.displayName = "Select";

export const SelectTrigger = Select;

export const SelectValue = ({ 
  placeholder, 
  children, 
  ...props 
}: { 
  placeholder?: string; 
  children?: React.ReactNode 
}) => (
  <span {...props}>{placeholder || children}</span>
);

export const SelectContent = ({ children, ...props }: { children?: React.ReactNode }) => (
  <div {...props}>{children}</div>
);

export const SelectItem = ({ 
  value, 
  children, 
  ...props 
}: { 
  value: string; 
  children?: React.ReactNode 
}) => (
  <option value={value} {...props}>
    {children}
  </option>
);