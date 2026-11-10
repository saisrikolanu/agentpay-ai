"use client";

import { useMemo, useState } from "react";
import { fetchProducts, sendChatMessage, submitCart } from "@/lib/api";
import type { Product } from "@/lib/types";

const DEMO_MESSAGE = "I need a work-from-home setup under $150. Prioritize comfort and productivity.";

export default function HomePage() {
  const [message, setMessage] = useState(DEMO_MESSAGE);
  const [response, setResponse] = useState<any>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [selected, setSelected] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recommendedProducts = useMemo(() => {
    if (!response?.recommendations) return [] as Array<Product & { reason: string }>;
    return response.recommendations
      .map((item: { product_id: string; reason: string }) => {
        const product = products.find((candidate) => candidate.id === item.product_id);
        return product ? { ...product, reason: item.reason } : null;
      })
      .filter(Boolean) as Array<Product & { reason: string }>;
  }, [response, products]);

  const total = recommendedProducts.reduce((sum, product) => sum + product.price, 0);

  const loadProducts = async () => {
    const data = await fetchProducts();
    setProducts(data);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await sendChatMessage(message);
      setResponse(result);
      await loadProducts();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!response) return;
    const chosenProducts = recommendedProducts.map((product) => ({
      product_id: product.id,
      quantity: selected[product.id] || 1,
    }));

    const result = await submitCart(1, chosenProducts, Number(response.budget.amount));
    if (!result.allowed) {
      setError("This cart exceeds the budget; adjust the selection.");
      return;
    }

    alert(`Approved cart ready. Total: $${result.total.toFixed(2)} (${result.message})`);
  };

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-6xl space-y-8">
        <header className="rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl shadow-slate-950/30">
          <p className="text-sm uppercase tracking-[0.25em] text-cyan-400">AgentPay</p>
          <h1 className="mt-2 text-4xl font-bold">AI shopping with a payment safety boundary</h1>
          <p className="mt-3 max-w-2xl text-slate-300">
            Recommend products, enforce spending limits, and require explicit user approval before the payment is created.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-700 bg-slate-900 p-6">
            <label htmlFor="shopping-request" className="mb-2 block text-sm font-medium text-slate-300">
              Shopping request
            </label>
            <textarea
              id="shopping-request"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              className="min-h-[120px] w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-slate-100"
            />
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="mt-4 rounded-xl bg-cyan-500 px-4 py-2 font-medium text-slate-950 disabled:opacity-60"
            >
              {loading ? "Thinking..." : "Ask AgentPay"}
            </button>
            {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
          </div>

          <div className="rounded-2xl border border-slate-700 bg-slate-900 p-6">
            <h2 className="text-xl font-semibold">Recommendation</h2>
            {response ? (
              <div className="mt-4 space-y-3 text-sm text-slate-200">
                <p>
                  <span className="font-medium text-cyan-400">Budget:</span> {response.budget.amount} {response.budget.currency}
                </p>
                <p>
                  <span className="font-medium text-cyan-400">Preferences:</span> {response.preferences.join(", ")}
                </p>
                <p className="text-slate-300">{response.explanation}</p>
                <div className="rounded-xl bg-slate-950 p-3 text-cyan-300">
                  {response.recommendations.map((item: any, index: number) => (
                    <div key={index} className="flex items-center justify-between gap-3 py-2">
                      <span>{item.product_id}</span>
                      <span className="text-right text-slate-300">{item.reason}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="mt-4 text-slate-400">No recommendations yet. Try the sample request.</p>
            )}
          </div>
        </section>

        {recommendedProducts.length > 0 && (
          <section className="rounded-2xl border border-slate-700 bg-slate-900 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Approved cart</h2>
              <div className="rounded-full bg-emerald-500/20 px-3 py-1 text-sm text-emerald-300">
                Total: ${total.toFixed(2)}
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {recommendedProducts.map((product) => (
                <div key={product.id} className="rounded-xl border border-slate-700 bg-slate-950 p-4">
                  <h3 className="font-semibold text-white">{product.name}</h3>
                  <p className="mt-2 text-sm text-slate-300">{product.reason}</p>
                  <div className="mt-3 flex items-center justify-between">
                    <span className="text-cyan-300">${product.price.toFixed(2)}</span>
                    <input
                      type="number"
                      min={1}
                      defaultValue={1}
                      onChange={(event) =>
                        setSelected((current) => ({
                          ...current,
                          [product.id]: Number(event.target.value),
                        }))
                      }
                      className="w-16 rounded border border-slate-700 bg-slate-900 px-2 py-1 text-right text-white"
                    />
                  </div>
                </div>
              ))}
            </div>
            <button
              onClick={handleApprove}
              className="mt-6 rounded-xl bg-emerald-500 px-4 py-2 font-medium text-slate-950"
            >
              Approve and continue to PayPal
            </button>
          </section>
        )}
      </div>
    </main>
  );
}
