const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Request failed");
  }

  return response.json() as Promise<T>;
}

export async function sendChatMessage(message: string) {
  return request<{ intent: string; budget: { amount: string; currency: string }; preferences: string[]; recommendations: Array<{ product_id: string; reason: string }>; explanation: string }>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export async function fetchProducts() {
  return request<Array<{ id: string; name: string; category: string; description: string; price: number; currency: string; available: number; features: string[] }>>("/api/products");
}

export async function submitCart(sessionId: number, products: Array<{ product_id: string; quantity: number }>, budget: number) {
  return request<{ cart_id: string; total: number; currency: string; allowed: boolean; message: string; items: Array<{ product_id: string; price: number; quantity: number }> }>('/api/carts', {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, products, budget }),
  });
}

export async function createPayPalOrder(items: Array<{ product_id: string; quantity: number }>, expectedAmount?: number, expectedCurrency = "USD") {
  return request<{ order_id: string; status: string; amount: string; currency: string; approval_url?: string }> ("/api/paypal/orders", {
    method: "POST",
    body: JSON.stringify({ items, expected_amount: expectedAmount, expected_currency: expectedCurrency }),
  });
}

export async function capturePayPalOrder(orderId: string, expectedAmount?: number | string, expectedCurrency = "USD") {
  return request<{ order_id: string; capture_id: string; status: string; amount: string; currency: string }>(`/api/paypal/orders/${orderId}/capture`, {
    method: "POST",
    body: JSON.stringify({ expected_amount: expectedAmount, expected_currency: expectedCurrency }),
  });
}
