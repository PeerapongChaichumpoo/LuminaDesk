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
       │   Popularity Recommender  │       │ SVD Factorization    (35%)  │
       │  + Regional Sales Weight  │       │ Collaborative Filter (25%)  │
       └───────────────────────────┘       │ Content-Based       (25%)  │
                                           │ Location-Aware      (15%)  │
                                           └─────────────────────────────┘
```

### 1. Switching Hybrid (Guest / Cold-Start Users)
- Automatically switches guests and cold-start users to global **Popularity Metrics** (order volume & quantity).
- Optionally blends regional location affinity if a shipping state is selected.

### 2. Weighted Hybrid (Returning Customers)
Combines normalized candidate scores dynamically across four specialized recommendation engines:
- **SVD Matrix Factorization (35% weight)**: Latent factor decomposition capturing hidden user preference vectors.
- **Collaborative Filtering (25% weight)**: Fast, on-demand User-User cosine similarity based on interaction matrices.
- **Content-Based Filtering (25% weight)**: Feature vector similarity derived from product categories, subcategories, pricing, and materials.
- **Location-Aware Regional Scoring (15% weight)**: State and regional purchasing affinity dynamics.

---

## 🚀 High-Performance Optimizations

- **Instant Boot Caching**: Binary dataset caching via `dataset.parquet` reduces Excel parsing overhead from ~10s to ~0.05s.
- **On-Demand Cosine Similarity**: Per-user query vector dot products avoid computing giant 17,000×17,000 similarity matrices at startup.
- **Sparse Storage**: Compressed Sparse Row (`scipy.sparse.csr_matrix`) serialization reduces cache footprint from 3.37 GB to **0.8 MB**.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn, Pandas, NumPy, SciPy, FastParquet
- **Frontend**: React 19, Vite, Vanilla CSS Design System with Modern Micro-Animations & Dark Aesthetics
- **Data & Assets**: Excel Transaction Logs (`Office Sales.xlsx`), Custom Product Visual Mapping (`product_images_output.csv`), Static Asset Hosting (`/images`)

---

## 🌐 API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/products` | GET | Retrieve complete product catalog with enriched sales metrics |
| `/api/products/recommendations/{customer_key}` | GET | Generate Hybrid Recommendations (Guest or Customer ID) |
| `/api/customers` | GET | List sample customers for customer context switching |
| `/images/{path}` | GET | Serve product visual assets |

---

## 📂 Project Repository Structure

```
LuminaDesk/
├── backend/
│   ├── main.py                  # FastAPI app entry point & route controllers
│   ├── requirements.txt         # Python dependencies
│   └── recommenders/            # Cleanly separated recommender algorithm modules
│       ├── popularity.py        # Popularity Recommender
│       ├── svd.py               # SVD Matrix Factorization Recommender
│       ├── collaborative.py     # User-Based Collaborative Filtering
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
