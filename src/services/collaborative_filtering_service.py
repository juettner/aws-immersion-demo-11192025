"""
Collaborative filtering recommendation service for concert recommendations.

This service implements user-based and item-based collaborative filtering
to generate concert recommendations based on historical attendance patterns.
"""
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import math
from datetime import datetime

from src.models.recommendation import (
    UserInteraction,
    RecommendationScore,
    RecommendationResult,
    SimilarityScore
)


class CollaborativeFilteringService:
    """
    Collaborative filtering recommendation engine.
    
    Implements both user-based and item-based collaborative filtering
    using cosine similarity and nearest neighbors approach.
    """
    
    def __init__(self):
        """Initialize the collaborative filtering service."""
        self.user_item_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.item_user_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.user_similarities: Dict[Tuple[str, str], float] = {}
        self.item_similarities: Dict[Tuple[str, str], float] = {}
        
    def add_interaction(self, interaction: UserInteraction) -> None:
        """
        Add a user-item interaction to the matrix.
        
        Args:
            interaction: User interaction data
        """
        user_id = interaction.user_id
        concert_id = interaction.concert_id
        strength = interaction.interaction_strength
        
        # Update user-item matrix
        self.user_item_matrix[user_id][concert_id] = strength
        
        # Update item-user matrix (transpose)
        self.item_user_matrix[concert_id][user_id] = strength
    
    def build_interaction_matrix(self, interactions: List[UserInteraction]) -> None:
        """
        Build user-item interaction matrix from historical data.
        
        Args:
            interactions: List of user interactions
        """
        self.user_item_matrix.clear()
        self.item_user_matrix.clear()
        
        for interaction in interactions:
            self.add_interaction(interaction)
    
    def calculate_cosine_similarity(
        self,
        vector1: Dict[str, float],
        vector2: Dict[str, float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vector1: First vector as dict
            vector2: Second vector as dict
            
        Returns:
            Cosine similarity score (-1 to 1)
        """
        # Find common items
        common_items = set(vector1.keys()) & set(vector2.keys())
        
        if not common_items:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(vector1[item] * vector2[item] for item in common_items)
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(val ** 2 for val in vector1.values()))
        magnitude2 = math.sqrt(sum(val ** 2 for val in vector2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def find_similar_users(
        self,
        user_id: str,
        top_k: int = 10,
        min_similarity: float = 0.1
    ) -> List[SimilarityScore]:
        """
        Find users similar to the given user using cosine similarity.
        
        Args:
            user_id: Target user ID
            top_k: Number of similar users to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar users with similarity scores
        """
        if user_id not in self.user_item_matrix:
            return []
        
        target_vector = self.user_item_matrix[user_id]
        similarities = []
        
        for other_user_id, other_vector in self.user_item_matrix.items():
            if other_user_id == user_id:
                continue
            
            similarity = self.calculate_cosine_similarity(target_vector, other_vector)
            
            if similarity >= min_similarity:
                similarities.append(
                    SimilarityScore(
                        id1=user_id,
                        id2=other_user_id,
                        similarity=similarity,
                        method="cosine"
                    )
                )
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x.similarity, reverse=True)
        return similarities[:top_k]
    
    def find_similar_items(
        self,
        concert_id: str,
        top_k: int = 10,
        min_similarity: float = 0.1
    ) -> List[SimilarityScore]:
        """
        Find concerts similar to the given concert based on user interactions.
        
        Args:
            concert_id: Target concert ID
            top_k: Number of similar concerts to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar concerts with similarity scores
        """
        if concert_id not in self.item_user_matrix:
            return []
        
        target_vector = self.item_user_matrix[concert_id]
        similarities = []
        
        for other_concert_id, other_vector in self.item_user_matrix.items():
            if other_concert_id == concert_id:
                continue
            
            similarity = self.calculate_cosine_similarity(target_vector, other_vector)
            
            if similarity >= min_similarity:
                similarities.append(
                    SimilarityScore(
                        id1=concert_id,
                        id2=other_concert_id,
                        similarity=similarity,
                        method="cosine"
                    )
                )
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x.similarity, reverse=True)
        return similarities[:top_k]
    
    def recommend_concerts_user_based(
        self,
        user_id: str,
        top_k: int = 10,
        num_neighbors: int = 20
    ) -> RecommendationResult:
        """
        Generate concert recommendations using user-based collaborative filtering.
        
        Finds similar users and recommends concerts they attended that the
        target user hasn't attended yet.
        
        Args:
            user_id: Target user ID
            top_k: Number of recommendations to return
            num_neighbors: Number of similar users to consider
            
        Returns:
            Recommendation result with scored concerts
        """
        # Find similar users
        similar_users = self.find_similar_users(user_id, top_k=num_neighbors)
        
        if not similar_users:
            return RecommendationResult(
                user_id=user_id,
                recommendations=[],
                algorithm="collaborative_user_based",
                total_candidates=0
            )
        
        # Get concerts the target user has already interacted with
        user_concerts = set(self.user_item_matrix.get(user_id, {}).keys())
        
        # Aggregate recommendations from similar users
        concert_scores: Dict[str, float] = defaultdict(float)
        concert_weights: Dict[str, float] = defaultdict(float)
        
        for similar_user in similar_users:
            similarity = similar_user.similarity
            other_user_id = similar_user.id2
            
            # Get concerts this similar user interacted with
            for concert_id, interaction_strength in self.user_item_matrix[other_user_id].items():
                # Skip concerts the target user already knows
                if concert_id in user_concerts:
                    continue
                
                # Weight the score by similarity and interaction strength
                concert_scores[concert_id] += similarity * interaction_strength
                concert_weights[concert_id] += similarity
        
        # Normalize scores
        recommendations = []
        for concert_id, total_score in concert_scores.items():
            if concert_weights[concert_id] > 0:
                normalized_score = total_score / concert_weights[concert_id]
                confidence = min(concert_weights[concert_id] / num_neighbors, 1.0)
                
                recommendations.append(
                    RecommendationScore(
                        item_id=concert_id,
                        item_type="concert",
                        score=normalized_score,
                        confidence=confidence,
                        reasoning=f"Based on {len(similar_users)} similar users"
                    )
                )
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return RecommendationResult(
            user_id=user_id,
            recommendations=recommendations[:top_k],
            algorithm="collaborative_user_based",
            total_candidates=len(concert_scores)
        )
    
    def recommend_concerts_item_based(
        self,
        user_id: str,
        top_k: int = 10,
        num_similar_items: int = 20
    ) -> RecommendationResult:
        """
        Generate concert recommendations using item-based collaborative filtering.
        
        Finds concerts similar to those the user has attended and recommends them.
        
        Args:
            user_id: Target user ID
            top_k: Number of recommendations to return
            num_similar_items: Number of similar items to consider per user concert
            
        Returns:
            Recommendation result with scored concerts
        """
        # Get concerts the user has interacted with
        user_concerts = self.user_item_matrix.get(user_id, {})
        
        if not user_concerts:
            return RecommendationResult(
                user_id=user_id,
                recommendations=[],
                algorithm="collaborative_item_based",
                total_candidates=0
            )
        
        # Aggregate recommendations from similar concerts
        concert_scores: Dict[str, float] = defaultdict(float)
        concert_weights: Dict[str, float] = defaultdict(float)
        
        for concert_id, user_interaction in user_concerts.items():
            # Find concerts similar to this one
            similar_concerts = self.find_similar_items(concert_id, top_k=num_similar_items)
            
            for similar_concert in similar_concerts:
                similar_id = similar_concert.id2
                similarity = similar_concert.similarity
                
                # Skip concerts the user already knows
                if similar_id in user_concerts:
                    continue
                
                # Weight by similarity and user's interaction with the source concert
                concert_scores[similar_id] += similarity * user_interaction
                concert_weights[similar_id] += similarity
        
        # Normalize scores
        recommendations = []
        for concert_id, total_score in concert_scores.items():
            if concert_weights[concert_id] > 0:
                normalized_score = total_score / concert_weights[concert_id]
                confidence = min(concert_weights[concert_id] / len(user_concerts), 1.0)
                
                recommendations.append(
                    RecommendationScore(
                        item_id=concert_id,
                        item_type="concert",
                        score=normalized_score,
                        confidence=confidence,
                        reasoning=f"Similar to {len(user_concerts)} concerts you attended"
                    )
                )
        
        # Sort by score and return top k
        recommendations.sort(key=lambda x: x.score, reverse=True)
        
        return RecommendationResult(
            user_id=user_id,
            recommendations=recommendations[:top_k],
            algorithm="collaborative_item_based",
            total_candidates=len(concert_scores)
        )
    
    def get_matrix_statistics(self) -> Dict:
        """
        Get statistics about the interaction matrix.
        
        Returns:
            Dictionary with matrix statistics
        """
        total_users = len(self.user_item_matrix)
        total_items = len(self.item_user_matrix)
        total_interactions = sum(
            len(concerts) for concerts in self.user_item_matrix.values()
        )
        
        # Calculate sparsity
        possible_interactions = total_users * total_items
        sparsity = 1.0 - (total_interactions / possible_interactions) if possible_interactions > 0 else 1.0
        
        # Average interactions per user
        avg_interactions_per_user = total_interactions / total_users if total_users > 0 else 0
        
        return {
            "total_users": total_users,
            "total_items": total_items,
            "total_interactions": total_interactions,
            "sparsity": sparsity,
            "avg_interactions_per_user": avg_interactions_per_user
        }
