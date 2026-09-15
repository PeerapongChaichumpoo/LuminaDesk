import pandas as pd
import numpy as np
from numpy.linalg import norm
from typing import List, Dict, Any
from scipy import sparse

from recommenders.cache_utils import load_cache, save_cache

class ItemCollaborativeFilteringRecommender:
    """
    Item-Based Collaborative Filtering using Cosine Similarity on matrix R^T (Item-Item).
    Predicts rating/preference for item i by user u based on similarity to items j purchased by user u:
    r_u_i = sum(sim(i, j) * r_u_j) / sum(|sim(i, j)|)
    """
    def __init__(self, top_k_items: int = 10):
        self.top_k_items = top_k_items
        self.df_ref = None
        self.R = None             # User x Item matrix (shape: n_users x n_items)
        self.norm_R_item = None   # Pre-normalized Item x User matrix (shape: n_items x n_users)
        self.user_mapper = {}
        self.user_inv_mapper = {}
        self.item_mapper = {}
        self.item_inv_mapper = {}

    def fit(self, df: pd.DataFrame, use_cache: bool = True):
        if df.empty:
            return

        self.df_ref = df

        if use_cache:
            cached = load_cache("item_cf_model")
            if cached and all(k in cached for k in ["R_sparse", "user_mapper", "item_mapper", "user_inv_mapper", "item_inv_mapper"]):
                self.R = cached["R_sparse"].toarray()
                self.user_mapper = cached["user_mapper"]
                self.item_mapper = cached["item_mapper"]
                self.user_inv_mapper = cached["user_inv_mapper"]
                self.item_inv_mapper = cached["item_inv_mapper"]
                self._precompute_item_norms()
                return

        grouped = df.groupby(['CustomerKey', 'ProductKey'])['OrderQuantity'].sum().reset_index()
        matrix_df = grouped.pivot(index='CustomerKey', columns='ProductKey', values='OrderQuantity').fillna(0)

        self.user_inv_mapper = {i: k for i, k in enumerate(matrix_df.index)}
        self.user_mapper = {k: i for i, k in enumerate(matrix_df.index)}
        self.item_inv_mapper = {i: str(k) for i, k in enumerate(matrix_df.columns)}
        self.item_mapper = {str(k): i for i, k in enumerate(matrix_df.columns)}

        self.R = matrix_df.values.astype(float)
        self._precompute_item_norms()

        # Cache sparse user-item matrix
        save_cache("item_cf_model", {
            "R_sparse": sparse.csr_matrix(self.R),
            "user_mapper": self.user_mapper,
            "item_mapper": self.item_mapper,
            "user_inv_mapper": self.user_inv_mapper,
            "item_inv_mapper": self.item_inv_mapper
        })

    def _precompute_item_norms(self):
        """Pre-normalize item vectors (rows of R^T) for fast item-item cosine similarity."""
        import time
        t0 = time.time()
        # R is (n_users, n_items). R.T is (n_items, n_users).
        R_T = self.R.T
        item_norms = norm(R_T, axis=1, keepdims=True)
        item_norms[item_norms == 0] = 1e-10
        self.norm_R_item = R_T / item_norms
        print(f"[Item-CF] Pre-normalized R^T (Item vectors) in {round(time.time()-t0, 3)}s")

    def predict_item_based(self, customer_key: int, limit: int = 20) -> List[Dict[str, Any]]:
        if customer_key not in self.user_mapper or self.R is None:
            return []

        u_idx = self.user_mapper[customer_key]
        user_ratings = self.R[u_idx, :]  # shape: (n_items,)

        purchased_indices = np.where(user_ratings > 0)[0]
        if len(purchased_indices) == 0:
            return []

        # Purchased item vectors & user interaction weights
        purchased_weights = user_ratings[purchased_indices]            # shape: (m,)
        purchased_item_vecs = self.norm_R_item[purchased_indices, :]    # shape: (m, n_users)

        # Compute cosine similarity matrix between ALL items and purchased items
        # self.norm_R_item is (n_items, n_users), purchased_item_vecs.T is (n_users, m)
        item_sims = np.dot(self.norm_R_item, purchased_item_vecs.T)     # shape: (n_items, m)

        # For each candidate item, consider only top-K most similar purchased items to reduce noise
        if item_sims.shape[1] > self.top_k_items:
            # Mask out non-top-K similarities per row
            top_k_mask = np.zeros_like(item_sims, dtype=bool)
            top_indices = np.argsort(item_sims, axis=1)[:, -self.top_k_items:]
            rows = np.arange(item_sims.shape[0])[:, None]
            top_k_mask[rows, top_indices] = True
            item_sims = np.where(top_k_mask, item_sims, 0.0)

        numerators = np.dot(item_sims, purchased_weights)               # shape: (n_items,)
        denominators = np.sum(np.abs(item_sims), axis=1)                # shape: (n_items,)
        denominators[denominators == 0] = 1e-10

        scores = numerators / denominators
        # Mask out already purchased items
        scores[purchased_indices] = -np.inf

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
item_cf_recommender = ItemCollaborativeFilteringRecommender()
