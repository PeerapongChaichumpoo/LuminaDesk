import pandas as pd
import numpy as np
from numpy.linalg import norm
from typing import List, Dict, Any

from recommenders.cache_utils import load_cache, save_cache

class SVDRecommender:
    """
    Singular Value Decomposition (SVD) Matrix Factorization.
    Decomposes User-Item interaction matrix R into U * Sigma * Vt using NumPy.
    """
    def __init__(self, n_components: int = 20):
        self.n_components = n_components
        self.user_mapper = {}
        self.item_mapper = {}
        self.item_inv_mapper = {}
        self.user_inv_mapper = {}
        self.U = None
        self.sigma = None
        self.Vt = None
        self.df_ref = None

    def fit(self, df: pd.DataFrame, use_cache: bool = True):
        if df.empty:
            return

        self.df_ref = df.copy()

        if use_cache:
            cached = load_cache("svd_model")
            if cached and all(k in cached for k in ["U", "sigma", "Vt", "user_mapper", "item_mapper", "user_inv_mapper", "item_inv_mapper"]):
                self.U = cached["U"]
                self.sigma = cached["sigma"]
                self.Vt = cached["Vt"]
                self.user_mapper = cached["user_mapper"]
                self.item_mapper = cached["item_mapper"]
                self.user_inv_mapper = cached["user_inv_mapper"]
                self.item_inv_mapper = cached["item_inv_mapper"]
                return

        # Build interaction matrix (CustomerKey x ProductKey) using OrderQuantity
        grouped = df.groupby(['CustomerKey', 'ProductKey'])['OrderQuantity'].sum().reset_index()
        matrix_df = grouped.pivot(index='CustomerKey', columns='ProductKey', values='OrderQuantity').fillna(0)

        self.user_inv_mapper = {i: k for i, k in enumerate(matrix_df.index)}
        self.user_mapper = {k: i for i, k in enumerate(matrix_df.index)}
        self.item_inv_mapper = {i: str(k) for i, k in enumerate(matrix_df.columns)}
        self.item_mapper = {str(k): i for i, k in enumerate(matrix_df.columns)}

        R = matrix_df.values.astype(float)

        # SVD Matrix Factorization using numpy linalg
        U, s, Vt = np.linalg.svd(R, full_matrices=False)

        k = min(self.n_components, len(s))
        self.U = U[:, :k]
        self.sigma = np.diag(s[:k])
        self.Vt = Vt[:k, :]

        save_cache("svd_model", {
            "U": self.U,
            "sigma": self.sigma,
            "Vt": self.Vt,
            "user_mapper": self.user_mapper,
            "item_mapper": self.item_mapper,
            "user_inv_mapper": self.user_inv_mapper,
            "item_inv_mapper": self.item_inv_mapper
        })

    def get_user_recommendations(self, customer_key: int, limit: int = 20) -> List[Dict[str, Any]]:
        """ Reconstructs user ratings: R_hat = U * Sigma * Vt """
        if customer_key not in self.user_mapper or self.U is None:
            return []

        user_idx = self.user_mapper[customer_key]
        user_pred = np.dot(np.dot(self.U[user_idx, :], self.sigma), self.Vt)

        interacted_keys = self.df_ref[self.df_ref['CustomerKey'] == customer_key]['ProductKey'].unique()
        interacted_indices = [
            self.item_mapper[str(k)] for k in interacted_keys
            if str(k) in self.item_mapper
        ]

        # Copy predictions and set purchased items to negative infinity
        scores = user_pred.copy()
        scores[interacted_indices] = -np.inf
        top_indices = np.argsort(scores)[::-1]

        # Score normalization to [0, 1] for valid top items
        valid_scores = scores[scores != -np.inf]
        max_s = valid_scores.max() if len(valid_scores) > 0 and valid_scores.max() > 0 else 1.0

        recs = []
        for idx in top_indices:
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

    def get_frequently_bought_together(self, product_key: str, limit: int = 5) -> List[Dict[str, Any]]:
        """ Item latent factor Cosine Similarity for complementary products """
        str_pk = str(product_key)
        if str_pk not in self.item_mapper or self.Vt is None:
            return []

        item_idx = self.item_mapper[str_pk]
        item_factors = self.Vt.T
        target_vector = item_factors[item_idx]

        norms = norm(item_factors, axis=1)
        target_norm = norm(target_vector)
        norms[norms == 0] = 1e-10
        target_norm = target_norm if target_norm != 0 else 1e-10

        similarities = np.dot(item_factors, target_vector) / (norms * target_norm)
        top_indices = np.argsort(similarities)[::-1]

        recs = []
        for idx in top_indices:
            if len(recs) >= limit:
                break
            sim_key = self.item_inv_mapper[idx]
            if sim_key != str_pk:
                prod_info = self.df_ref[self.df_ref['ProductKey'].astype(str) == sim_key].iloc[0]
                recs.append({
                    "ProductKey": sim_key,
                    "ProductName": prod_info["ProductName"],
                    "CategoryName": prod_info["CategoryName"],
                    "SubcategoryName": prod_info["SubcategoryName"],
                    "UnitPrice": float(prod_info["UnitPrice"]),
                    "similarity": round(float(similarities[idx]), 4)
                })

        return recs

# Global singleton
svd_recommender = SVDRecommender()
