import React from "react";

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary";
}

export function Button({ children, onClick, variant = "primary" }: ButtonProps) {
  return (
    <button onClick={onClick} data-variant={variant}>
      {children}
    </button>
  );
}
