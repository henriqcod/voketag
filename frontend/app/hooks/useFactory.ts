"use client";

import { useState, useEffect } from "react";
import { factoryAPI } from "@/lib/api-client";

interface Product {
  id?: string;
  name: string;
  description: string;
  timestamp?: string;
}

interface Batch {
  id?: string;
  name: string;
  quantity: number;
  timestamp?: string;
}

export function useProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await factoryAPI.getProducts();
      setProducts(data.products || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar produtos");
    } finally {
      setLoading(false);
    }
  };

  const createProduct = async (product: Omit<Product, "id" | "timestamp">) => {
    setLoading(true);
    setError(null);
    try {
      const newProduct = await factoryAPI.createProduct(product);
      setProducts(prev => [...prev, newProduct]);
      return newProduct;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar produto");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  return {
    products,
    loading,
    error,
    fetchProducts,
    createProduct,
  };
}

export function useBatches() {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBatches = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await factoryAPI.getBatches();
      setBatches(data.batches || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar lotes");
    } finally {
      setLoading(false);
    }
  };

  const createBatch = async (batch: Omit<Batch, "id" | "timestamp">) => {
    setLoading(true);
    setError(null);
    try {
      const newBatch = await factoryAPI.createBatch(batch);
      setBatches(prev => [...prev, newBatch]);
      return newBatch;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar lote");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  return {
    batches,
    loading,
    error,
    fetchBatches,
    createBatch,
  };
}