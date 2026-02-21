import { NextRequest, NextResponse } from "next/server";

const FACTORY_API_URL =
  process.env.FACTORY_API_URL ||
  process.env.NEXT_PUBLIC_FACTORY_API_URL ||
  "http://localhost:8081";
const FACTORY_JWT = process.env.FACTORY_JWT;

export async function GET(request: NextRequest) {
  if (!FACTORY_JWT) {
    return NextResponse.json(
      { error: "FACTORY_JWT não configurado", products: [] },
      { status: 200 }
    );
  }

  const { searchParams } = new URL(request.url);
  const skip = searchParams.get("skip") ?? "0";
  const limit = searchParams.get("limit") ?? "20";

  const headers: HeadersInit = {
    Authorization: `Bearer ${FACTORY_JWT}`,
    "Content-Type": "application/json",
  };

  try {
    const res = await fetch(
      `${FACTORY_API_URL}/v1/products?skip=${skip}&limit=${limit}`,
      { headers }
    );
    const products = res.ok ? await res.json() : [];

    if (!res.ok) {
      return NextResponse.json(
        {
          error: res.status === 401 ? "Token factory inválido ou expirado" : "Erro ao listar produtos",
          products: [],
        },
        { status: 200 }
      );
    }

    return NextResponse.json({ products, error: null });
  } catch (e) {
    const message = e instanceof Error ? e.message : "Erro de conexão com Factory API";
    return NextResponse.json(
      { error: message, products: [] },
      { status: 200 }
    );
  }
}
