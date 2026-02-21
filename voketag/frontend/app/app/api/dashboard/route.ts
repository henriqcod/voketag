import { NextResponse } from "next/server";

const ADMIN_API_URL =
  process.env.ADMIN_API_URL ||
  process.env.NEXT_PUBLIC_ADMIN_API_URL ||
  "http://localhost:8082";
const ADMIN_JWT = process.env.ADMIN_JWT;

export async function GET() {
  if (!ADMIN_JWT) {
    return NextResponse.json(
      { error: "ADMIN_JWT não configurado", stats: null, recentUsers: [] },
      { status: 200 }
    );
  }

  const headers: HeadersInit = {
    Authorization: `Bearer ${ADMIN_JWT}`,
    "Content-Type": "application/json",
  };

  try {
    const [statsRes, usersRes] = await Promise.all([
      fetch(`${ADMIN_API_URL}/v1/admin/dashboard?days=365`, { headers }),
      fetch(`${ADMIN_API_URL}/v1/admin/users?skip=0&limit=5`, { headers }),
    ]);

    const stats = statsRes.ok ? await statsRes.json() : null;
    const recentUsers = usersRes.ok ? await usersRes.json() : [];

    if (!statsRes.ok) {
      return NextResponse.json(
        {
          error: statsRes.status === 401 ? "Token admin inválido ou expirado" : "Erro ao carregar dashboard",
          stats,
          recentUsers,
        },
        { status: 200 }
      );
    }

    return NextResponse.json({ stats, recentUsers, error: null });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Erro de conexão com Admin API";
    return NextResponse.json(
      { error: message, stats: null, recentUsers: [] },
      { status: 200 }
    );
  }
}
