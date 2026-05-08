from fastapi import FastAPI
from openai import OpenAI
import os
from dotenv import load_dotenv

from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, engine
from models import Base, Product
from sqlalchemy.orm import Session

# =========================
# LOAD ENV
# =========================
load_dotenv()

# =========================
# APP
# =========================
app = FastAPI()

# =========================
# CORS FIX
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# OPENAI
# =========================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# CREATE TABLES
# =========================
Base.metadata.create_all(bind=engine)

# =========================
# HOME
# =========================
@app.get("/")
def home():
    return {"message": "AI SaaS is running 🚀"}

# =========================
# ANALYZE PRODUCT
# =========================
@app.post("/analyze")
def analyze_product(product: dict):

    db: Session = SessionLocal()

    try:
        prompt = f"""
You are a TikTok ecommerce expert.

Analyze this product:

Name: {product['name']}
Trend: {product['trend']}/10
Competition: {product['competition']}/10
Margin: {product['margin']}%

Return ONLY:

Verdict: WINNER or AVOID
Reason: short
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content

        # SCORE
        score = (
            product['trend'] * 5 +
            product['margin'] * 1.5 -
            product['competition'] * 4
        )

        score = max(0, min(100, round(score)))

        verdict = (
            "WINNER"
            if "WINNER" in result.upper()
            else "AVOID"
        )

        # SAVE DB
        new_product = Product(
            name=product['name'],
            verdict=verdict,
            score=score,
            result=result
        )

        db.add(new_product)
        db.commit()

        return {
            "name": product['name'],
            "verdict": verdict,
            "score": score,
            "result": result
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()

# =========================
# GET PRODUCTS
# =========================
@app.get("/products")
def get_products():

    db: Session = SessionLocal()

    try:
        products = db.query(Product).all()
        return products

    finally:
        db.close()