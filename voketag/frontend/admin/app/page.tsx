"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api-client";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = getToken();
    if (token) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0f172a]">
      <p className="text-[#94a3b8]">Redirecionando...</p>
    </div>
  );
}
