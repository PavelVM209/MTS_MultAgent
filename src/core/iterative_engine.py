"""
Iterative Improvement Engine for MTS_MultAgent

This module provides the core iterative improvement engine that enables agents
to automatically refine their results until quality thresholds are met.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Tuple

from .llm_client import LLMClient, IterationResult, get_llm_client
from .quality_metrics import QualityEvaluator, ConvergenceCriteria
from .base_agent import BaseAgent


class IterativeEngine(BaseAgent):
    """
    Core engine for iterative improvement across all agents.
    
    This engine manages the iterative refinement process, ensuring that results
    meet quality thresholds before being returned to the user.
    """
    
    def __init__(self, 
                 llm_client: Optional[LLMClient] = None,
                 quality_evaluator: Optional[QualityEvaluator] = None,
                 convergence_criteria: Optional[ConvergenceCriteria] = None):
        super().__init__("IterativeEngine")
        
        self.llm_client = llm_client or get_llm_client()
        self.quality_evaluator = quality_evaluator or QualityEvaluator(self.llm_client)
        self.convergence_criteria = convergence_criteria or ConvergenceCriteria()
        
        # Performance metrics
        self.metrics = {
            "iterations_total": 0,
            "converged_runs": 0,
            "max_iterations_reached": 0,
            "avg_iterations_per_run": 0,
            "total_improvement_time": 0
        }
        
    async def improve_until_convergence(
        self,
        initial_data: Dict[str, Any],
        improve_function: Callable,
        expected_context: str,
        task_requirements: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IterationResult:
        """
        Iteratively improve data until convergence or max iterations.
        
        Args:
            initial_data: Starting data for improvement
            improve_function: Function that takes data and returns improved version
            expected_context: Original context for quality evaluation
            task_requirements: Specific requirements for the task
            metadata: Additional metadata for tracking
            
        Returns:
            IterationResult with final data and improvement history
        """
        start_time = time.time()
        current_iteration = 0
        best_data = initial_data.copy()
        best_quality = 0.0
        quality_history = []
        improvement_history = []
        
        self.logger.info("Starting iterative improvement process")
        
        while current_iteration < self.convergence_criteria.max_iterations:
            try:
                # Evaluate current quality
                current_quality = await self._evaluate_quality(
                    best_data, expected_context, task_requirements
                )
                
                quality_history.append(current_quality)
                
                self.logger.info(
                    f"Iteration {current_iteration}: Quality score = {current_quality:.1f}%"
                )
                
                # Check convergence criteria
                should_stop, stop_reason = self.convergence_criteria.should_stop(quality_history)
                
                if should_stop:
                    self.logger.info(f"Convergence reached: {stop_reason}")
                    self.metrics["converged_runs"] += 1
                    break
                
                # Generate improvements if not converged
                if current_iteration < self.convergence_criteria.max_iterations - 1:
                    improvements = await self._generate_improvements(
                        best_data, current_quality, current_iteration, expected_context
                    )
                    
                    improved_data = await improve_function(best_data, improvements)
                    
                    # Evaluate improvement
                    new_quality = await self._evaluate_quality(
                        improved_data, expected_context, task_requirements
                    )
                    
                    if new_quality > current_quality:
                        # Accept improvements
                        best_data = improved_data
                        best_quality = new_quality
                        improvement_history.append({
                            "iteration": current_iteration,
                            "improvements": improvements,
                            "quality_before": current_quality,
                            "quality_after": new_quality,
                            "improvement_delta": new_quality - current_quality
                        })
                        
                        self.logger.info(
                            f"Iteration {current_iteration}: Improved by {new_quality - current_quality:.1f}%"
                        )
                    else:
                        # No improvement, but continue
                        improvement_history.append({
                            "iteration": current_iteration,
                            "improvements": improvements,
                            "quality_before": current_quality,
                            "quality_after": new_quality,
                            "improvement_delta": new_quality - current_quality,
                            "accepted": False
                        })
                        
                        self.logger.info(
                            f"Iteration {current_iteration}: No improvement ({new_quality:.1f}% vs {current_quality:.1f}%)"
                        )
                
                current_iteration += 1
                
            except Exception as e:
                self.logger.error(f"Error in iteration {current_iteration}: {e}")
                break
        
        # Final evaluation
        final_quality = await self._evaluate_quality(
            best_data, expected_context, task_requirements
        )
        
        # Update metrics
        self.metrics["iterations_total"] += current_iteration + 1
        self.metrics["total_improvement_time"] += time.time() - start_time
        
        if current_iteration >= self.convergence_criteria.max_iterations - 1:
            self.metrics["max_iterations_reached"] += 1
        
        # Generate final feedback
        final_feedback = await self._generate_final_feedback(
            quality_history, improvement_history, stop_reason if 'stop_reason' in locals() else "Max iterations"
        )
        
        result = IterationResult(
            iteration=current_iteration,
            quality_score=final_quality,
            data=best_data,
            feedback=final_feedback,
            needs_refinement=final_quality < self.convergence_criteria.quality_threshold,
            improvements_made=[imp.get("improvements", "") for imp in improvement_history if imp.get("accepted", True)],
            convergence_detected="Converged" in stop_reason if 'stop_reason' in locals() else False
        )
        
        self.logger.info(
            f"Iterative improvement completed: {current_iteration + 1} iterations, "
            f"final quality: {final_quality:.1f}%"
        )
        
        return result
    
    async def _evaluate_quality(
        self,
        data: Dict[str, Any],
        expected_context: str,
        task_requirements: Optional[List[str]] = None
    ) -> float:
        """Evaluate quality of current data."""
        try:
            metrics = await self.quality_evaluator.evaluate_comprehensive(
                data, expected_context, task_requirements
            )
            return metrics.overall_quality
        except Exception as e:
            self.logger.error(f"Error evaluating quality: {e}")
            return 50.0  # Default middle score
    
    async def _generate_improvements(
        self,
        current_data: Dict[str, Any],
        current_quality: float,
        iteration: int,
        expected_context: str
    ) -> str:
        """Generate improvement suggestions using LLM."""
        try:
            improvements = await self.llm_client.generate_improvements(
                current_data, 
                f"Current quality score: {current_quality:.1f}%. Target: {self.convergence_criteria.quality_threshold}%",
                iteration
            )
            return improvements
        except Exception as e:
            self.logger.error(f"Error generating improvements: {e}")
            return "Continue with standard analysis approach"
    
    async def _generate_final_feedback(
        self,
        quality_history: List[float],
        improvement_history: List[Dict[str, Any]],
        stop_reason: str
    ) -> str:
        """Generate comprehensive feedback for the iterative process."""
        
        # Calculate statistics
        iterations = len(quality_history)
        initial_quality = quality_history[0] if quality_history else 0
        final_quality = quality_history[-1] if quality_history else 0
        total_improvement = final_quality - initial_quality
        
        best_iteration = max(range(len(quality_history)), key=lambda i: quality_history[i])
        best_quality = quality_history[best_iteration]
        
        feedback_parts = [
            f"🔄 **Итеративное улучшение завершено**: {iterations} итераций",
            f"📊 **Качество**: {initial_quality:.1f}% → {final_quality:.1f}% (улучшение на {total_improvement:+.1f}%)",
            f"🏆 **Лучший результат**: {best_quality:.1f}% на итерации {best_iteration}",
            f"🛑 **Причина остановки**: {stop_reason}"
        ]
        
        # Analyze improvement patterns
        if len(improvement_history) > 1:
            positive_improvements = sum(1 for imp in improvement_history if imp.get("improvement_delta", 0) > 0)
            feedback_parts.append(f"✅ **Успешных улучшений**: {positive_improvements}/{len(improvement_history)}")
        
        # Convergence analysis
        if len(quality_history) >= 3:
            recent_improvements = [
                quality_history[i] - quality_history[i-1]
                for i in range(1, min(3, len(quality_history)))
            ]
            avg_recent_improvement = sum(recent_improvements) / len(recent_improvements)
            feedback_parts.append(f"📈 **Тренд последних улучшений**: {avg_recent_improvement:+.2f}%")
        
        return " | ".join(feedback_parts)
    
    async def parallel_improve(
        self,
        data_variants: List[Dict[str, Any]],
        improve_function: Callable,
        expected_context: str,
        task_requirements: Optional[List[str]] = None
    ) -> IterationResult:
        """
        Run multiple improvement processes in parallel and select the best result.
        
        Useful when exploring different improvement strategies.
        """
        self.logger.info(f"Starting parallel improvement for {len(data_variants)} variants")
        
        # Create tasks for parallel execution
        tasks = [
            self.improve_until_convergence(
                variant, improve_function, expected_context, task_requirements
            )
            for variant in data_variants
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and find best result
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Parallel improvement {i} failed: {result}")
            else:
                valid_results.append(result)
        
        if not valid_results:
            raise RuntimeError("All parallel improvement processes failed")
        
        # Select best result by quality score
        best_result = max(valid_results, key=lambda r: r.quality_score)
        
        # Add parallel execution info
        best_result.feedback += f" | 🏆 **Лучший из {len(valid_results)} параллельных процессов**"
        
        self.logger.info(
            f"Parallel improvement completed: Best quality = {best_result.quality_score:.1f}%"
        )
        
        return best_result
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current engine metrics."""
        total_runs = self.metrics["converged_runs"] + self.metrics["max_iterations_reached"]
        
        if total_runs > 0:
            avg_iterations = self.metrics["iterations_total"] / total_runs
        else:
            avg_iterations = 0
        
        return {
            **self.metrics,
            "total_runs": total_runs,
            "convergence_rate": (self.metrics["converged_runs"] / total_runs * 100) if total_runs > 0 else 0,
            "avg_iterations_per_run": avg_iterations,
            "avg_time_per_run": self.metrics["total_improvement_time"] / total_runs if total_runs > 0 else 0
        }
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = {
            "iterations_total": 0,
            "converged_runs": 0,
            "max_iterations_reached": 0,
            "avg_iterations_per_run": 0,
            "total_improvement_time": 0
        }


class AdaptiveConvergenceCriteria(ConvergenceCriteria):
    """
    Adaptive convergence criteria that adjusts based on performance.
    """
    
    def __init__(self, initial_quality_threshold: float = 85.0):
        super().__init__(quality_threshold=initial_quality_threshold)
        self.initial_quality_threshold = initial_quality_threshold
        self.performance_history = []
        
    def adjust_threshold(self, recent_quality_scores: List[float]):
        """Adjust quality threshold based on recent performance."""
        if len(recent_quality_scores) >= 5:
            avg_recent_quality = sum(recent_quality_scores[-5:]) / 5
            
            # If consistently achieving high quality, raise threshold
            if avg_recent_quality > self.quality_threshold + 5:
                self.quality_threshold = min(95, self.quality_threshold + 2)
            
            # If consistently failing to meet threshold, lower it slightly
            elif avg_recent_quality < self.quality_threshold - 10:
                self.quality_threshold = max(70, self.quality_threshold - 2)
            
            self.performance_history.append(avg_recent_quality)


# Global engine instance
_iterative_engine: Optional[IterativeEngine] = None


def get_iterative_engine() -> IterativeEngine:
    """Get global iterative engine instance."""
    global _iterative_engine
    if _iterative_engine is None:
        _iterative_engine = IterativeEngine()
    return _iterative_engine


async def improve_until_convergence(
    initial_data: Dict[str, Any],
    improve_function: Callable,
    expected_context: str,
    task_requirements: Optional[List[str]] = None
) -> IterationResult:
    """Convenience function for iterative improvement."""
    engine = get_iterative_engine()
    return await engine.improve_until_convergence(
        initial_data, improve_function, expected_context, task_requirements
    )
