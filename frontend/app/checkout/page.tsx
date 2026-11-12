"use client";

import { useEffect, useState } from "react";
import { capturePayPalOrder } from "@/lib/api";

export default function CheckoutPage() {
  const [status, setStatus] = useState("Processing your PayPal approval...");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const paypalStatus = params.get("paypal");
    const orderId = sessionStorage.getItem("agentpay_order_id");

    if (paypalStatus === "cancelled") {
      setStatus("PayPal checkout was cancelled. No payment was captured.");
      setLoading(false);
      return;
    }

    if (!orderId) {
      setStatus("No approved PayPal order was found for this checkout session.");
      setError("The PayPal order was not found in the current session.");
      setLoading(false);
      return;
    }

    const expectedAmount = sessionStorage.getItem("agentpay_expected_amount");
    const expectedCurrency = sessionStorage.getItem("agentpay_expected_currency") ?? "USD";

    capturePayPalOrder(orderId, expectedAmount ?? undefined, expectedCurrency)
      .then((result) => {
        setStatus(`Payment captured successfully. Order ${result.order_id} is now ${result.status}.`);
        sessionStorage.removeItem("agentpay_order_id");
        sessionStorage.removeItem("agentpay_expected_amount");
        sessionStorage.removeItem("agentpay_expected_currency");
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Unable to capture the PayPal order.");
        setStatus("PayPal payment capture failed.");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto max-w-xl rounded-2xl border border-slate-700 bg-slate-900 p-8">
        <h1 className="text-2xl font-semibold">PayPal checkout</h1>
        <p className="mt-4 text-slate-300">{status}</p>
        {loading && <p className="mt-4 text-sm text-cyan-300">Finalizing payment...</p>}
        {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
      </div>
    </main>
  );
}
