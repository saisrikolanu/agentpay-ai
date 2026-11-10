# AgentPay

AI-powered purchasing assistant with spending safeguards and PayPal sandbox checkout.

## Stack

- Frontend: Next.js + TypeScript + Tailwind
- Backend: FastAPI + SQLAlchemy + SQLite
- AI: rule-based product recommendation with optional OpenAI extension
- Payments: PayPal sandbox flow

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Demo request

"I need a work-from-home setup under $150. Prioritize comfort and productivity."

## Notes

This MVP uses a seeded catalog and sandbox-safe order logic. Real PayPal credentials are required for live payment execution.
