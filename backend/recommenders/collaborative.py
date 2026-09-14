import pandas as pd
import numpy as np
from numpy.linalg import norm
from typing import List, Dict, Any
from scipy import sparse

from recommenders.cache_utils import load_cache, save_cache

class CollaborativeFilteringRecommender:
    """
    User-Based Collaborative Filtering using Cosine Similarity.
    Predicts rating/preference for item i by user u:
    r_u_i = sum(sim(u, v) * r_v_i) / sum(|sim(u, v)|)
    
    Uses on-demand similarity computation (per-user query) to avoid
    precomputing the full N×N similarity matrix at startup.
    """
    def __init__(self, k_neighbors: int = 5):
        self.k_neighbors = k_neighbors
        self.df_ref = None
        self.R = None
        self.norm_R_user = None  # Pre-normalized R for fast on-demand cosine sim
        self.user_mapper = {}
        self.user_inv_mapper = {}
        self.item_mapper = {}
        self.item_inv_mapper = {}

    def fit(self, df: pd.DataFrame, use_cache: bool = True):
        if df.empty:
            return

        self.df_ref = df

        if use_cache:
            cached = load_cache("cf_model")
            if cached and all(k in cached for k in ["R_sparse", "user_mapper", "item_mapper", "user_inv_mapper", "item_inv_mapper"]):
                self.R = cached["R_sparse"].toarray()  # sparse -> dense
                self.user_mapper = cached["user_mapper"]
                self.item_mapper = cached["item_mapper"]
                self.user_inv_mapper = cached["user_inv_mapper"]
                self.item_inv_mapper = cached["item_inv_mapper"]
                self._precompute_norms()
                return

        grouped = df.groupby(['CustomerKey', 'ProductKey'])['OrderQuantity'].sum().reset_index()
        matrix_df = grouped.pivot(index='CustomerKey', columns='ProductKey', values='OrderQuantity').fillna(0)

        self.user_inv_mapper = {i: k for i, k in enumerate(matrix_df.index)}
        self.user_mapper = {k: i for i, k in enumerate(matrix_df.index)}
        self.item_inv_mapper = {i: str(k) for i, k in enumerate(matrix_df.columns)}
        self.item_mapper = {str(k): i for i, k in enumerate(matrix_df.columns)}

        self.R = matrix_df.values.astype(float)
        self._precompute_norms()

        # Cache R as sparse CSR (~0.8 MB instead of 768 MB dense)
        save_cache("cf_model", {
            "R_sparse": sparse.csr_matrix(self.R),
            "user_mapper": self.user_mapper,
            "item_mapper": self.item_mapper,
            "user_inv_mapper": self.user_inv_mapper,
            "item_inv_mapper": self.item_inv_mapper
        })

    def _precompute_norms(self):
        """Pre-normalize R rows for fast on-demand cosine similarity (~0.05s)."""
        import time
        t0 = time.time()
        user_norms = norm(self.R, axis=1, keepdims=True)
        user_norms[user_norms == 0] = 1e-10
        self.norm_R_user = self.R / user_norms
        print(f"[CF] Pre-normalized R for on-demand similarity in {round(time.time()-t0, 3)}s")

    def _get_user_similarities(self, u_idx: int) -> np.ndarray:
        """Compute cosine similarity of user u_idx against all users on-demand."""
        return np.dot(self.norm_R_user, self.norm_R_user[u_idx])

    def predict_user_based(self, customer_key: int, limit: int = 20) -> List[Dict[str, Any]]:
        if customer_key not in self.user_mapper or self.R is None:
            return []

        u_idx = self.user_mapper[customer_key]
        sims = self._get_user_similarities(u_idx)

        # Top-K neighbors excluding self
        top_neighbors = np.argsort(sims)[::-1]
        top_neighbors = [idx for idx in top_neighbors if idx != u_idx][:self.k_neighbors]

        neighbor_sims = sims[top_neighbors]
        neighbor_ratings = self.R[top_neighbors, :]

        sim_sum = np.sum(np.abs(neighbor_sims))
        if sim_sum == 0:
            sim_sum = 1e-10

        predicted_ratings = np.dot(neighbor_sims, neighbor_ratings) / sim_sum

        # Exclude interacted items
        interacted_keys = self.df_ref[self.df_ref['CustomerKey'] == customer_key]['ProductKey'].unique()
        interacted_indices = [
            self.item_mapper[str(k)] for k in interacted_keys
            if str(k) in self.item_mapper
        ]

        scores = predicted_ratings.copy()
        scores[interacted_indices] = -np.inf
        top_item_indices = np.argsort(scores)[::-1]

        valid_scores = scores[scores != -np.inf]
        max_s = valid_scores.max() if len(valid_scores) > 0 and valid_scores.max() > 0 else 1.0

        recs = []
        for idx in top_item_indices:
            if len(recs) >= limit:
                break
            if scores[idx] == -np.inf:
                continue
            pk = self.item_inv_mapper[idx]
            prod_info = self.df_ref[self.df_ref['ProductKey'].astype(str) == pk].iloc[0]
            norm_score = max(0.0, float(scores[idx] / max_s))
            recs.append({
                "ProductKey": pk,
                "ProductName": prod_info["ProductName"],
                "CategoryName": prod_info["CategoryName"],
                "SubcategoryName": prod_info["SubcategoryName"],
                "UnitPrice": float(prod_info["UnitPrice"]),
                "score": round(norm_score, 4)
            })

        return recs

# Global singleton
cf_recommender = CollaborativeFilteringRecommender()
