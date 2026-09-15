import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import random
import datetime


# Import cleanly separated recommender modules
from recommenders.popularity import popularity_recommender
from recommenders.svd import svd_recommender
from recommenders.collaborative import cf_recommender
from recommenders.item_collaborative import item_cf_recommender
from recommenders.content_based import content_recommender
from recommenders.location_aware import location_recommender
from recommenders.hybrid_recommender import hybrid_recommender

from fastapi.staticfiles import StaticFiles

import logging

# Filter out static image request logs (/images/...) to keep terminal output clean
class StaticImageFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "/images/" not in record.getMessage()

logging.getLogger("uvicorn.access").addFilter(StaticImageFilter())

app = FastAPI(title="Lumina Workspace Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

IMAGES_STATIC_DIR = os.path.join(PROJECT_ROOT, "images")
if os.path.exists(IMAGES_STATIC_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_STATIC_DIR), name="images")

DATA_PATH = os.path.join(PROJECT_ROOT, "Office Sales.xlsx")

df = pd.DataFrame()
popular_cache = []

MATERIALS_LIST = [
    "Solid Wood",
    "Leather & Mesh",
    "Steel Frame",
    "Ergonomic Polymer",
    "Natural Oak & Teak",
    "Stainless Steel"
]

ASSEMBLY_MAP = [
    "None - Fully Assembled",
    "15 Mins - Minimal Toolless Assembly",
    "30 Mins - Standard Hardware Assembly",
    "45 Mins - White-Glove Professional Assembly Recommended"
]

SUBCATEGORY_IMAGE_PRESETS = {
    "Chairs": [
        "https://images.unsplash.com/photo-1580481072645-022f9a6d8310?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1505797149-43b0069ec26b?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?auto=format&fit=crop&w=800&q=80"
    ],
    "Tables": [
        "https://images.unsplash.com/photo-1530018607912-eff2daa1bac4?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80"
    ],
    "Bookcases": [
        "https://images.unsplash.com/photo-1594620302200-9a762244a156?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1595428774223-ef52624120d2?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1544457070-4cd773b4d71e?auto=format&fit=crop&w=800&q=80"
    ],
    "Furnishings": [
        "https://images.unsplash.com/photo-1540574163026-643ea20ade25?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=800&q=80"
    ],
    "Storage": [
        "https://images.unsplash.com/photo-1595428774223-ef52624120d2?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1544457070-4cd773b4d71e?auto=format&fit=crop&w=800&q=80"
    ],
    "Appliances": [
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80"
    ],
    "Accessories": [
        "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80"
    ]
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1580481072645-022f9a6d8310?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1540574163026-643ea20ade25?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?auto=format&fit=crop&w=800&q=80"
]

import os
import os.path

CUSTOM_IMAGE_MAP = {}
IMAGE_CSV_PATH = r"c:\Users\Lenovo\Desktop\1_2026 Slides\CSX4207_DecisionSupport_recommendor\Project\product_images_output.csv"

def load_custom_image_map():
    global CUSTOM_IMAGE_MAP
    if os.path.exists(IMAGE_CSV_PATH):
        try:
            img_df = pd.read_csv(IMAGE_CSV_PATH)
            for _, crow in img_df.iterrows():
                pk = str(crow.get("ProductKey", ""))
                img_url = crow.get("image_url", None)
                img_url2 = crow.get("image_url2", None)
                img_url3 = crow.get("image_url3", None)
                
                urls = []
                if pd.notna(img_url) and str(img_url).strip():
                    urls.append(str(img_url).strip())
                if pd.notna(img_url2) and str(img_url2).strip():
                    urls.append(str(img_url2).strip())
                if pd.notna(img_url3) and str(img_url3).strip():
                    urls.append(str(img_url3).strip())
                    
                if pk and urls:
                    CUSTOM_IMAGE_MAP[pk] = urls
            print(f"Loaded {len(CUSTOM_IMAGE_MAP)} custom product image URLs from CSV.")
        except Exception as e:
            print(f"Could not load custom image CSV: {e}")

load_custom_image_map()

def enrich_product(record: dict) -> dict:
    """ Enriches raw pandas records with Lumina furniture metadata """
    p_key = str(record.get("ProductKey", ""))
    key_hash = hash(p_key)
    
    cat = record.get("CategoryName", "Furniture")
    sub = record.get("SubcategoryName", "Furnishings")
    material = MATERIALS_LIST[abs(key_hash) % len(MATERIALS_LIST)]
    
    price = float(record.get("UnitPrice", 199.0))
    stock = 2 + (abs(key_hash) % 28)
    
    assembly = ASSEMBLY_MAP[abs(key_hash) % len(ASSEMBLY_MAP)]
    
    if p_key in CUSTOM_IMAGE_MAP and len(CUSTOM_IMAGE_MAP[p_key]) > 0:
        c_urls = CUSTOM_IMAGE_MAP[p_key]
        primary_img = c_urls[0]
        secondary_img = c_urls[1] if len(c_urls) > 1 else c_urls[0]
        tertiary_img = c_urls[2] if len(c_urls) > 2 else c_urls[0]
    else:
        img_list = SUBCATEGORY_IMAGE_PRESETS.get(sub, FALLBACK_IMAGES)
        primary_img = img_list[abs(key_hash) % len(img_list)]
        secondary_img = img_list[(abs(key_hash) + 1) % len(img_list)]
        tertiary_img = FALLBACK_IMAGES[(abs(key_hash) + 2) % len(FALLBACK_IMAGES)]
    
    original_price = round(price * 1.2, 2) if (abs(key_hash) % 3 == 0) else None

    res = {
        "ProductKey": str(record.get("ProductKey")),
        "ProductName": record.get("ProductName"),
        "CategoryName": cat,
        "SubcategoryName": sub,
        "UnitPrice": price,
        "originalPrice": original_price,
        "stockCount": stock,
        "inStock": stock > 0,
        "material": material,
        "dimensions": {
            "width": f"{20 + (abs(key_hash) % 40)} in",
            "depth": f"{18 + (abs(key_hash) % 24)} in",
            "height": f"{30 + (abs(key_hash) % 35)} in",
            "weight": f"{15 + (abs(key_hash) % 65)} lbs"
        },
        "assembly": assembly,
        "warranty": "10-Year Limited Commercial Warranty",
        "image": primary_img,
        "images": [
            primary_img,
            secondary_img,
            tertiary_img
        ]
    }
    if "score" in record:
        res["score"] = record["score"]
    if "hybrid_score" in record:
        res["score"] = record["hybrid_score"]
    if "similarity_score" in record:
        res["similarityScore"] = record["similarity_score"]
    if "similarity" in record:
        res["similarity"] = record["similarity"]
        res["similarityScore"] = record["similarity"]
    if "svd_score" in record:
        res["svdScore"] = record["svd_score"]
    if "user_cf_score" in record:
        res["userCfScore"] = record["user_cf_score"]
    if "item_cf_score" in record:
        res["itemCfScore"] = record["item_cf_score"]
    if "content_score" in record:
        res["contentScore"] = record["content_score"]
    if "loc_score" in record:
        res["locScore"] = record["loc_score"]
    if "location" in record:
        res["location"] = record["location"]
    
    prod_key = str(record.get("ProductKey", ""))
    pop_lookup = getattr(popularity_recommender, "lookup_dict", {})
    pop_info = pop_lookup.get(prod_key)

    total_qty = record.get("total_quantity") or (pop_info.get("total_quantity") if pop_info else None)
    sales_cnt = record.get("sales_count") or (pop_info.get("sales_count") if pop_info else None)
    sales_rnk = record.get("sales_rank") or (pop_info.get("sales_rank") if pop_info else None)

    if total_qty is not None:
        res["total_quantity"] = int(total_qty)
        res["totalQuantity"] = int(total_qty)
    if sales_cnt is not None:
        res["sales_count"] = int(sales_cnt)
        res["salesCount"] = int(sales_cnt)
    if sales_rnk is not None:
        res["salesRank"] = int(sales_rnk)
    return res

@app.on_event("startup")
def load_data():
    global df, popular_cache
    import time
    boot_start = time.time()
    try:
        cache_dir = os.path.join(BASE_DIR, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        parquet_path = os.path.join(cache_dir, "dataset.parquet")

        t0 = time.time()
        if os.path.exists(parquet_path):
            print("Loading cached dataset from dataset.parquet...")
            df = pd.read_parquet(parquet_path)
        else:
            print("Reading original Excel dataset...")
            try:
                df = pd.read_excel(DATA_PATH, engine="calamine")
            except Exception:
                df = pd.read_excel(DATA_PATH)
            try:
                df.to_parquet(parquet_path, index=False)
                print("Saved dataset cache to dataset.parquet")
            except Exception as pe:
                print(f"Could not save parquet cache: {pe}")
        print(f"  -> Dataset loaded in {round(time.time()-t0, 3)}s ({len(df)} rows)")

        t1 = time.time()
        print("Fitting Modular Hybrid Recommenders (Popularity, SVD, User-CF, Item-CF, Content, Location)...")
        hybrid_recommender.fit(df)
        print(f"  -> All models fitted in {round(time.time()-t1, 3)}s")

        t2 = time.time()
        raw_popular = popularity_recommender.get_recommendations(limit=20)
        popular_cache = [enrich_product(p) for p in raw_popular]
        print(f"  -> Popular cache built in {round(time.time()-t2, 3)}s")

        total = round(time.time() - boot_start, 3)
        print(f"✅ All Recommender Models Trained Successfully. Total boot: {total}s")
        
    except Exception as e:
        print(f"Error initializing backend: {e}")

@app.get("/api/products")
def get_products(limit: int = 10000):
    if df.empty: return []
    raw = df.drop_duplicates(subset=["ProductKey"]).head(limit).to_dict(orient="records")
    return [enrich_product(r) for r in raw]

@app.get("/api/recommendations/{customer_key}")
@app.get("/api/products/recommendations/{customer_key}")
def get_recommendations_endpoint(
    customer_key: str,
    location: Optional[str] = Query("California"),
    w_svd: Optional[float] = Query(None),
    w_user_cf: Optional[float] = Query(None),
    w_item_cf: Optional[float] = Query(None),
    w_content: Optional[float] = Query(None),
    w_loc: Optional[float] = Query(None)
):
    """
    Modular Hybrid Recommendation Endpoint:
    1. Switching Hybrid: Guest -> Popularity Recommender.
    2. Weighted Hybrid: Returning Customer -> SVD + Item-CF + User-CF + Content + Location (5% default).
    """
    res = hybrid_recommender.get_recommendations(
        customer_key,
        location=location,
        limit=20,
        w_svd=w_svd,
        w_user_cf=w_user_cf,
        w_item_cf=w_item_cf,
        w_content=w_content,
        w_loc=w_loc
    )
    enriched_recs = [enrich_product(r) for r in res.get("recommendations", [])]
    return {
        "type": res.get("hybrid_type", "hybrid"),
        "message": res.get("message", ""),
        "weights": res.get("weights", {}),
        "recommendations": enriched_recs
    }

@app.get("/api/products/popularity")
def get_popularity_endpoint(limit: int = 20):
    """ Global Popularity Recommendations (Cold-Start) """
    raw = popularity_recommender.get_recommendations(limit=limit)
    return [enrich_product(r) for r in raw]

@app.get("/api/products/svd/{customer_key}")
def get_svd_endpoint(customer_key: int, limit: int = 20):
    """ SVD Matrix Factorization Recommendations """
    raw = svd_recommender.get_user_recommendations(customer_key, limit=limit)
    return [enrich_product(r) for r in raw]

@app.get("/api/products/collaborative/{customer_key}")
def get_user_collaborative_recommendations(customer_key: int, limit: int = 20):
    """ User-Based Collaborative Filtering Recommendations """
    raw = cf_recommender.predict_user_based(customer_key, limit=limit)
    return [enrich_product(r) for r in raw]

@app.get("/api/products/item-collaborative/{customer_key}")
def get_item_collaborative_recommendations(customer_key: int, limit: int = 20):
    """ Item-Based Collaborative Filtering Recommendations """
    raw = item_cf_recommender.predict_item_based(customer_key, limit=limit)
    return [enrich_product(r) for r in raw]


@app.get("/api/products/location-aware")
def get_location_aware_endpoint(location: str = Query("California"), limit: int = 20):
    """ Location-Aware Recommendations """
    raw = location_recommender.get_recommendations(location=location, limit=limit)
    return [enrich_product(r) for r in raw]


@app.get("/api/products/similar/{product_key}")
def get_similar_endpoint(product_key: str, limit: int = 5, exclude: Optional[str] = Query(None)):
    """ Content-Based Cosine Similarity recommendation """
    if df.empty: return []
    exclude_list = [str(x).strip() for x in exclude.split(",")] if exclude else []
    exclude_list.append(str(product_key))
    
    raw = content_recommender.get_similar_items(product_key, limit=limit + len(exclude_list))
    filtered = [enrich_product(r) for r in raw if str(r["ProductKey"]) not in exclude_list]
    return filtered[:limit]

@app.get("/api/products/frequently-bought-together/{product_key}")
def get_fbt_endpoint(product_key: str, limit: int = 4, exclude: Optional[str] = Query(None)):
    """ SVD Item Factor Cosine Similarity """
    exclude_list = [str(x).strip() for x in exclude.split(",")] if exclude else []
    exclude_list.append(str(product_key))
    
    recs = svd_recommender.get_frequently_bought_together(product_key, limit=limit + len(exclude_list))
    if not recs:
        raw_pop = popularity_recommender.get_recommendations(limit=limit + len(exclude_list))
        recs = [enrich_product(p) for p in raw_pop]

    filtered = [enrich_product(r) for r in recs if str(r.get("ProductKey")) not in exclude_list]
    return filtered[:limit]

@app.get("/api/history/{customer_key}")
def get_user_history(customer_key: int):
    if df.empty:
        raise HTTPException(status_code=500, detail="Data not loaded")
    user_history = df[df['CustomerKey'] == customer_key]
    if user_history.empty:
        return []
    user_unique = user_history.drop_duplicates(subset=["ProductKey"]).head(10).to_dict(orient="records")
    return [enrich_product(r) for r in user_unique]

# --- Checkout API ---
class CartItemModel(BaseModel):
    ProductKey: str
    ProductName: str
    UnitPrice: float
    quantity: Optional[int] = 1

class CheckoutRequest(BaseModel):
    customerKey: Optional[str] = "guest"
    shippingAddress: dict
    paymentMethod: str
    promoCode: Optional[str] = ""
    items: List[CartItemModel]

@app.post("/api/checkout")
def checkout_endpoint(req: CheckoutRequest):
    subtotal = sum(item.UnitPrice * (item.quantity or 1) for item in req.items)
    discount = 0.0
    if req.promoCode and req.promoCode.strip().upper() == "LUMINA10":
        discount = round(subtotal * 0.10, 2)
    
    taxable = max(0.0, subtotal - discount)
    tax = round(taxable * 0.08, 2)
    shipping = 0.0 if taxable >= 199.0 else 49.0
    total = round(taxable + tax + shipping, 2)

    order_id = f"LUMINA-{random.randint(100000, 999999)}"
    order_date = datetime.datetime.now().strftime("%B %d, %Y")

    return {
        "success": True,
        "orderId": order_id,
        "date": order_date,
        "subtotal": f"{subtotal:.2f}",
        "discount": f"{discount:.2f}",
        "tax": f"{tax:.2f}",
        "shipping": f"{shipping:.2f}",
        "total": f"{total:.2f}",
        "items": [item.dict() for item in req.items],
        "shippingAddress": req.shippingAddress,
        "paymentMethod": req.paymentMethod
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
