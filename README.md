# LuminaDesk - Executive Workspace & Modular Hybrid Recommendation Engine

> **LuminaDesk** is an executive furniture & workspace e-commerce platform powered by a **Modular Hybrid Recommendation Engine** designed in alignment with Chapter 10 Recommendation System principles.

---

## ⚡ Quick Start & Run Instructions

> [!IMPORTANT]
> **Always start the Backend first** so the API endpoints and recommender models are warm and ready before opening the frontend.

### 1. Start the Backend Server (FastAPI)

```bash
# Navigate to the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run the backend server
python main.py
```
*The backend will initialize datasets and recommenders. Thanks to built-in Parquet & model caching, startup completes in **< 1 second**.*

*The backend server will run at: `http://localhost:8000`*

---

### 2. Start the Frontend Application (React + Vite)

```bash
# Open a new terminal tab/window and navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
*The frontend application will be available at: `http://localhost:5173`*

---

## 🏗️ Recommender System Architecture

LuminaDesk implements a state-of-the-art **Modular Hybrid Recommendation Strategy** (Chapter 10):

```
                       ┌────────────────────────────────┐
                       │    Customer Shopping Context   │
                       └───────────────┬────────────────┘
                                       │
                    Is Customer a Guest or Cold-Start?
                                  /         \
                             Yes /           \ No
                                /             \
       ┌───────────────────────────┐       ┌─────────────────────────────┐
       │     SWITCHING HYBRID      │       │       WEIGHTED HYBRID       │
       │   Popularity Recommender  │       │ SVD Factorization    (30%)  │
       │  + Explicit Sales Rank    │       │ Item-Based CF (Rᵀ)   (25%)  │
       │  + Sales Volume & Count   │       │ User-Based CF (Peer) (20%)  │
       └───────────────────────────┘       │ Content-Based        (20%)  │
                                           │ Location-Aware       (5%)   │
                                           └─────────────────────────────┘
```

### 1. Switching Hybrid (Guest / Cold-Start Users)
- Automatically switches guests (`customerKey === 'new'`) to global **Popularity Metrics** derived from order quantities and transaction frequencies.
- Renders explicit gold sales badges (`🔥 Rank #X in Sales`, `📦 X Sold`) on product cards.
- Provides a dedicated **Cold-Start Popularity Breakdown Modal** displaying total sales volume and order frequency metrics.

### 2. Weighted Hybrid (Returning Customers)
Combines normalized candidate scores dynamically across five specialized recommendation algorithms:
- **SVD Matrix Factorization (30% weight):** Latent factor decomposition capturing hidden user preference vectors.
- **Item-Based Collaborative Filtering (25% weight):** Transposed interaction matrix $R^T$ cosine similarity identifying items frequently bought together across transactions.
- **User-Based Collaborative Filtering (20% weight):** On-demand User-User cosine similarity matching peer buyers with similar purchase habits.
- **Content-Based Filtering (20% weight):** Feature vector similarity derived from product categories, subcategories, pricing, and materials.
- **Location-Aware Regional Scoring (5% weight):** State and regional purchasing affinity dynamics (*configured as the lowest weighted component*).

---

## 🎨 Interactive Explainability & UI Features

- **Dynamic Hybrid Weight Adjustment Panel:** Interactive UI sliders allowing real-time tuning of algorithm weights (`SVD`, `Item-CF`, `User-CF`, `Content`, `Location`) with instant recommendation recalculation.
- **Centered Algorithmic Score Inspection Modal:** Centered viewport overlay with dark frosted glass backdrop (`backdrop-filter: blur(6px)`), providing color-coded score progress bars for returning customers and popularity volume stats for guests.
- **Title-Based Product Deduplication:** Strict normalization (`String.trim().toLowerCase()`) ensuring 100% unique items across recommendation lists.
- **Direct PDP "Buy Now" Checkout Modal:** Seamless 3-step Lumina Executive Checkout wizard launched directly from Product Detail Pages.

---

## 🚀 High-Performance Optimizations

- **Instant Boot Caching:** Binary dataset caching via `dataset.parquet` reduces Excel parsing overhead from ~10s to ~0.05s.
- **On-Demand Cosine Similarity:** Per-query vector dot products avoid computing giant similarity matrices at startup.
- **Sparse Matrix Storage:** Compressed Sparse Row (`scipy.sparse.csr_matrix`) serialization reduces cache footprint from 3.37 GB to **0.8 MB**.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI, Uvicorn, Pandas, NumPy, SciPy, FastParquet
- **Frontend:** React 19, Vite, Vanilla CSS Executive Design System (Ivory & Gold Aesthetics)
- **Data & Assets:** Excel Transaction Logs (`Office Sales.xlsx`), Custom Product Visual Mapping (`product_images_output.csv`), Static Asset Hosting (`/images`)

---

## 🌐 API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/products` | GET | Retrieve complete product catalog with enriched sales metrics |
| `/api/products/recommendations/{customer_key}` | GET | Generate Hybrid Recommendations (supports dynamic weight query params) |
| `/api/products/item-collaborative/{customer_key}` | GET | Isolated Item-Based Collaborative Filtering predictions |
| `/api/customers` | GET | List sample customers for context switching |
| `/images/{path}` | GET | Serve product visual assets |

---

## 📂 Project Repository Structure

```
LuminaDesk/
├── backend/
│   ├── main.py                  # FastAPI app entry point & route controllers
│   ├── requirements.txt         # Python dependencies
│   └── recommenders/            # Cleanly separated recommender algorithm modules
│       ├── popularity.py        # Popularity Recommender (Sales Rank & Volume)
│       ├── svd.py               # SVD Matrix Factorization Recommender
│       ├── item_collaborative.py# Item-Based CF (Rᵀ Co-Purchase Cosine Similarity)
│       ├── collaborative.py     # User-Based Collaborative Filtering (Peer Sim)
│       ├── content_based.py     # Content-Based Similarity Recommender
│       ├── location_aware.py    # Regional / State Affinity Recommender
│       ├── hybrid_recommender.py# Chapter 10 Hybrid Switch & Weighted Orchestrator
│       └── cache_utils.py       # Serialization & timing utilities
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/                     # React UI components, Cart Drawer & Search filters
├── images/                      # Local product visual assets
├── Office Sales.xlsx            # Primary sales transaction dataset
├── product_images_output.csv    # Product key to image mapping table
├── README.md                    # System documentation and setup guide
└── .gitignore                   # Excluded build artifacts and caches
```
