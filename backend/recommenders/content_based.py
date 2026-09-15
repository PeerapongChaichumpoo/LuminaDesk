import pandas as pd
import numpy as np
from numpy.linalg import norm
from typing import List, Dict, Any

from recommenders.cache_utils import load_cache, save_cache

class ContentBasedRecommender:
    """
    Content-Based Recommendation using Cosine Similarity on feature vectors.
    Builds feature representations from Category, Subcategory, and Price.
    Can recommend similar items for a target item OR user profile vector based on past purchases.
    """
    def __init__(self):
        self.df_ref = None
        self.feature_matrix = None
        self.item_mapper = {}
        self.item_inv_mapper = {}

    def fit(self, df: pd.DataFrame, use_cache: bool = True):
        if df.empty:
            return

        self.df_ref = df.drop_duplicates(subset=["ProductKey"]).copy().reset_index(drop=True)

        if use_cache:
            cached = load_cache("content_model")
            if cached and all(k in cached for k in ["feature_matrix", "item_mapper", "item_inv_mapper"]):
                self.feature_matrix = cached["feature_matrix"]
                self.item_mapper = cached["item_mapper"]
                self.item_inv_mapper = cached["item_inv_mapper"]
                return

        self.item_mapper = {str(pk): i for i, pk in enumerate(self.df_ref["ProductKey"])}
        self.item_inv_mapper = {i: str(pk) for i, pk in enumerate(self.df_ref["ProductKey"])}

        # Build feature matrix
        # 1. One-hot encode categories and subcategories
        cat_dummies = pd.get_dummies(self.df_ref["CategoryName"], prefix="cat")
        sub_dummies = pd.get_dummies(self.df_ref["SubcategoryName"], prefix="sub")

        # 2. Price normalized feature (0 to 1 scaling)
        prices = self.df_ref["UnitPrice"].values.astype(float)
        max_price = prices.max() if prices.max() > 0 else 1.0
        norm_prices = (prices / max_price).reshape(-1, 1)

        # 3. Concatenate feature vectors
        features = np.hstack([cat_dummies.values, sub_dummies.values, norm_prices])

        # Normalize feature vectors for cosine similarity computation
        norms = norm(features, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        self.feature_matrix = features / norms

        save_cache("content_model", {
            "feature_matrix": self.feature_matrix,
            "item_mapper": self.item_mapper,
            "item_inv_mapper": self.item_inv_mapper
        })

    def get_similar_items(self, product_key: str, limit: int = 5) -> List[Dict[str, Any]]:
        str_key = str(product_key)
        if self.feature_matrix is None or str_key not in self.item_mapper:
            return []

        target_idx = self.item_mapper[str_key]
        target_vec = self.feature_matrix[target_idx]

        similarities = np.dot(self.feature_matrix, target_vec)
        sorted_indices = np.argsort(similarities)[::-1]

        recs = []
        seen_names = set()
        target_row = self.df_ref.iloc[target_idx]
        if "ProductName" in target_row:
            seen_names.add(str(target_row["ProductName"]).strip().lower())

        for idx in sorted_indices:
            if len(recs) >= limit:
                break
            candidate_key = self.item_inv_mapper[idx]
            if candidate_key != str_key:
                row = self.df_ref.iloc[idx]
                p_name = str(row["ProductName"]).strip()
                if p_name.lower() in seen_names:
                    continue
                seen_names.add(p_name.lower())
                recs.append({
                    "ProductKey": candidate_key,
                    "ProductName": p_name,
                    "CategoryName": row["CategoryName"],
                    "SubcategoryName": row["SubcategoryName"],
                    "UnitPrice": float(row["UnitPrice"]),
                    "similarity_score": round(float(similarities[idx]), 4),
                    "score": round(float(similarities[idx]), 4)
                })

        return recs

    def get_user_content_recommendations(self, df_full: pd.DataFrame, customer_key: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Builds user content profile from past purchases and scores unpurchased candidate items.
        """
        if self.feature_matrix is None or df_full.empty:
            return []

        user_history = df_full[df_full['CustomerKey'] == customer_key]
        if user_history.empty:
            return []

        purchased_keys = [str(k) for k in user_history['ProductKey'].unique()]
        purchased_indices = [self.item_mapper[k] for k in purchased_keys if k in self.item_mapper]

        if not purchased_indices:
            return []

        # Average feature vector of purchased items (user profile)
        user_profile = np.mean(self.feature_matrix[purchased_indices], axis=0)
        profile_norm = norm(user_profile)
        if profile_norm > 0:
            user_profile = user_profile / profile_norm

        similarities = np.dot(self.feature_matrix, user_profile)
        
        # Filter already purchased items
        scores = similarities.copy()
        scores[purchased_indices] = -np.inf

        sorted_indices = np.argsort(scores)[::-1]
        valid_scores = scores[scores != -np.inf]
        max_s = valid_scores.max() if len(valid_scores) > 0 and valid_scores.max() > 0 else 1.0

        recs = []
        for idx in sorted_indices:
            if len(recs) >= limit:
                break
            if scores[idx] == -np.inf:
                continue
            candidate_key = self.item_inv_mapper[idx]
            row = self.df_ref.iloc[idx]
            norm_score = max(0.0, float(scores[idx] / max_s))
            recs.append({
                "ProductKey": candidate_key,
                "ProductName": row["ProductName"],
                "CategoryName": row["CategoryName"],
                "SubcategoryName": row["SubcategoryName"],
                "UnitPrice": float(row["UnitPrice"]),
                "score": round(norm_score, 4)
            })

        return recs

# Global singleton
content_recommender = ContentBasedRecommender()
