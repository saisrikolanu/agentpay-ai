export type Product = {
  id: string;
  name: string;
  category: string;
  description: string;
  price: number;
  currency: string;
  available: number;
  features: string[];
};

export type Recommendation = {
  product_id: string;
  reason: string;
};

export type ChatResult = {
  intent: string;
  budget: { amount: string; currency: string };
  preferences: string[];
  recommendations: Recommendation[];
  explanation: string;
};

export type CartResult = {
  cart_id: string;
  session_id: number;
  items: Array<{ product_id: string; price: number; quantity: number }>;
  total: number;
  currency: string;
  allowed: boolean;
  message: string;
};
