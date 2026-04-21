"""
Менеджер контекста ролей для интеграции с агентами анализа.

Этот модуль предоставляет улучшенный интерфейс для работы с ролями сотрудников
в контексте анализа совещаний и задач, обогащая базовые модели дополнительной
функциональностью для LLM агентов.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import json
from datetime import datetime

from .role_models import (
    RoleContextManager as BaseRoleContextManager,
    EmployeeProfile,
    RoleType,
    ActivityLevel,
    AnalysisRules,
    TeamStructure
)


class RoleAnalysisContext:
    """Контекст анализа для конкретного сотрудника."""
    
    def __init__(self, employee: EmployeeProfile, analysis_rules: Optional[AnalysisRules] = None):
        self.employee = employee
        self.analysis_rules = analysis_rules
        self.context_data: Dict[str, Any] = {}
        
    def get_llm_context(self) -> str:
        """
        Получить контекст для LLM анализа.
        
        Returns:
            Отформатированный контекст для использования в промптах
        """
        context_parts = []
        
        # Базовая информация
        context_parts.append(f"Сотрудник: {self.employee.display_name}")
        context_parts.append(f"Роль: {self._get_role_description()}")
        context_parts.append(f"Уровень активности: {self._get_activity_description()}")
        
        # Навыки и специализации
        if self.employee.skills.primary:
            context_parts.append(f"Ключевые навыки: {', '.join(self.employee.skills.primary)}")
        
        if self.employee.specializations:
            context_parts.append(f"Специализации: {', '.join(self.employee.specializations)}")
        
        # Стиль коммуникации
        if self.employee.communication_style:
            context_parts.append(f"Стиль коммуникации: {self.employee.communication_style}")
        
        # Правила анализа
        if self.analysis_rules:
            context_parts.append(f"Фокусные области: {', '.join(self.analysis_rules.focus_areas)}")
            if self.analysis_rules.expected_behaviors:
                context_parts.append(f"Ожидаемое поведение: {', '.join(self.analysis_rules.expected_behaviors)}")
        
        return "\n".join(context_parts)
    
    def _get_role_description(self) -> str:
        """Получить описание роли на русском."""
        role_descriptions = {
            RoleType.TECH_LEAD: "Технический лидер",
            RoleType.DEVOPS_ENGINEER: "DevOps инженер", 
            RoleType.DATA_ENGINEER: "Data инженер",
            RoleType.PRODUCT_OWNER: "Product Owner",
            RoleType.ANALYST: "Аналитик"
        }
        return role_descriptions.get(self.employee.role, "Неизвестная роль")
    
    def _get_activity_description(self) -> str:
        """Получить описание уровня активности."""
        activity_descriptions = {
            ActivityLevel.HIGH: "Высокая",
            ActivityLevel.MEDIUM_HIGH: "Выше среднего", 
            ActivityLevel.MEDIUM: "Средняя",
            ActivityLevel.LOW: "Низкая"
        }
        return activity_descriptions.get(self.employee.activity_level, "Неизвестная")
    
    def add_context_data(self, key: str, value: Any) -> None:
        """Добавить дополнительные данные контекста."""
        self.context_data[key] = value
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Получить сводку контекста."""
        return {
            "employee_id": self.employee.employee_id,
            "display_name": self.employee.display_name,
            "role": self.employee.role.value,
            "activity_level": self.employee.activity_level.value,
            "is_decision_maker": self.employee.is_decision_maker(),
            "is_high_activity": self.employee.is_high_activity(),
            "team_influence": self.employee.team_influence,
            "focus_areas": self.analysis_rules.focus_areas if self.analysis_rules else [],
            "context_data": self.context_data
        }


class EmployeeRoleManager:
    """Улучшенный менеджер ролей для интеграции с агентами."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Инициализация менеджера ролей.
        
        Args:
            config_path: Путь к файлу конфигурации roles.yaml
        """
        # Формируем правильный путь к roles.yaml от корня проекта
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "roles.yaml"
        
        self.base_manager = BaseRoleContextManager(config_path)
        self._analysis_contexts: Dict[str, RoleAnalysisContext] = {}
        
    def get_employee_context(self, identifier: str) -> Optional[RoleAnalysisContext]:
        """
        Получить контекст анализа для сотрудника.
        
        Args:
            identifier: ID, Jira имя или отображаемое имя сотрудника
            
        Returns:
            Контекст анализа или None если сотрудник не найден
        """
        employee = self.base_manager.get_employee(identifier)
        if not employee:
            return None
        
        # Получаем правила анализа для роли
        analysis_rules = self.base_manager.get_analysis_rules(employee.role)
        
        # Создаем или получаем из кэша
        context_key = employee.employee_id
        if context_key not in self._analysis_contexts:
            self._analysis_contexts[context_key] = RoleAnalysisContext(employee, analysis_rules)
        
        return self._analysis_contexts[context_key]
    
    def get_team_context(self) -> Dict[str, Any]:
        """
        Получить контекст всей команды.
        
        Returns:
            Словарь с информацией о команде
        """
        team_structure = self.base_manager.get_team_structure()
        if not team_structure:
            return {}
        
        all_employees = self.base_manager.get_all_employees()
        decision_makers = self.base_manager.get_decision_makers()
        high_activity = self.base_manager.get_high_activity_employees()
        
        return {
            "team_name": team_structure.name,
            "project": team_structure.project,
            "department": team_structure.department,
            "team_lead": team_structure.team_lead,
            "total_employees": len(all_employees),
            "decision_makers": [emp.display_name for emp in decision_makers],
            "high_activity_employees": [emp.display_name for emp in high_activity],
            "role_statistics": self.base_manager.get_role_statistics(),
            "activity_statistics": self.base_manager.get_activity_statistics()
        }
    
    def get_employees_for_analysis(self, role_filter: Optional[List[RoleType]] = None,
                                 activity_filter: Optional[List[ActivityLevel]] = None) -> List[RoleAnalysisContext]:
        """
        Получить список сотрудников для анализа с фильтрами.
        
        Args:
            role_filter: Фильтр по ролям
            activity_filter: Фильтр по уровню активности
            
        Returns:
            Список контекстов сотрудников
        """
        contexts = []
        
        for employee in self.base_manager.get_all_employees():
            # Применяем фильтры
            if role_filter and employee.role not in role_filter:
                continue
                
            if activity_filter and employee.activity_level not in activity_filter:
                continue
            
            context = self.get_employee_context(employee.employee_id)
            if context:
                contexts.append(context)
        
        return contexts
    
    def enhance_meeting_analysis(self, participant_names: List[str]) -> Dict[str, Any]:
        """
        Обогатить анализ совещания контекстом ролей.
        
        Args:
            participant_names: Список имен участников совещания
            
        Returns:
            Обогащенные данные для анализа
        """
        participant_contexts = {}
        identified_participants = []
        unidentified_participants = []
        
        for name in participant_names:
            context = self.get_employee_context(name)
            if context:
                participant_contexts[name] = context
                identified_participants.append(name)
            else:
                unidentified_participants.append(name)
        
        return {
            "total_participants": len(participant_names),
            "identified_participants": identified_participants,
            "unidentified_participants": unidentified_participants,
            "identification_rate": len(identified_participants) / len(participant_names) if participant_names else 0,
            "participant_contexts": {name: ctx.get_llm_context() for name, ctx in participant_contexts.items()},
            "decision_makers_present": [name for name, ctx in participant_contexts.items() 
                                     if ctx.employee.is_decision_maker()],
            "high_activity_present": [name for name, ctx in participant_contexts.items() 
                                    if ctx.employee.is_high_activity()]
        }
    
    def enhance_task_analysis(self, assignee_name: str) -> Dict[str, Any]:
        """
        Обогатить анализ задач контекстом ролей.
        
        Args:
            assignee_name: Имя исполнителя задачи
            
        Returns:
            Обогащенные данные для анализа
        """
        context = self.get_employee_context(assignee_name)
        
        if not context:
            return {
                "assignee_identified": False,
                "assignee_name": assignee_name,
                "role_context": None,
                "analysis_focus_areas": [],
                "expected_behaviors": []
            }
        
        analysis_rules = context.analysis_rules
        return {
            "assignee_identified": True,
            "assignee_name": assignee_name,
            "role_context": context.get_llm_context(),
            "analysis_focus_areas": analysis_rules.focus_areas if analysis_rules else [],
            "expected_behaviors": analysis_rules.expected_behaviors if analysis_rules else [],
            "communication_indicators": analysis_rules.communication_indicators if analysis_rules else [],
            "is_decision_maker": context.employee.is_decision_maker(),
            "activity_level": context.employee.activity_level.value,
            "specializations": context.employee.specializations
        }
    
    def get_role_based_prompts(self, role_type: RoleType) -> Dict[str, str]:
        """
        Получить промпты для анализа на основе роли.
        
        Args:
            role_type: Тип роли
            
        Returns:
            Словарь с промптами для разных типов анализа
        """
        role_def = self.base_manager.get_role_definition(role_type)
        analysis_rules = self.base_manager.get_analysis_rules(role_type)
        
        if not role_def:
            return {}
        
        prompts = {
            "meeting_analysis": self._generate_meeting_prompt(role_def, analysis_rules),
            "task_analysis": self._generate_task_prompt(role_def, analysis_rules),
            "performance_review": self._generate_performance_prompt(role_def, analysis_rules)
        }
        
        return prompts
    
    def _generate_meeting_prompt(self, role_def, analysis_rules) -> str:
        """Сгенерировать промпт для анализа совещаний."""
        prompt_parts = [
            f"Анализ участия сотрудника с ролью '{role_def.description}'.",
            f"Ключевые обязанности: {', '.join(role_def.responsibilities)}."
        ]
        
        if analysis_rules:
            prompt_parts.append(f"Фокусные области: {', '.join(analysis_rules.focus_areas)}.")
            prompt_parts.append(f"Ожидаемое поведение: {', '.join(analysis_rules.expected_behaviors)}.")
        
        return " ".join(prompt_parts)
    
    def _generate_task_prompt(self, role_def, analysis_rules) -> str:
        """Сгенерировать промпт для анализа задач."""
        prompt_parts = [
            f"Анализ выполнения задач сотрудником с ролью '{role_def.description}'.",
        ]
        
        if analysis_rules:
            prompt_parts.append(f"Критерии оценки: {', '.join(analysis_rules.expected_behaviors)}.")
        
        return " ".join(prompt_parts)
    
    def _generate_performance_prompt(self, role_def, analysis_rules) -> str:
        """Сгенерировать промпт для оценки производительности."""
        prompt_parts = [
            f"Оценка производительности сотрудника с ролью '{role_def.description}'.",
            f"Полномочия принятия решений: {role_def.decision_authority.value}."
        ]
        
        if analysis_rules:
            prompt_parts.append(f"Индикаторы коммуникации: {', '.join(analysis_rules.communication_indicators)}.")
        
        return " ".join(prompt_parts)
    
    def export_context_summary(self, output_path: Path) -> None:
        """
        Экспортировать сводку контекста в JSON файл.
        
        Args:
            output_path: Путь для сохранения файла
        """
        summary = {
            "export_timestamp": datetime.now().isoformat(),
            "team_context": self.get_team_context(),
            "employees": []
        }
        
        for employee in self.base_manager.get_all_employees():
            context = self.get_employee_context(employee.employee_id)
            if context:
                summary["employees"].append(context.get_context_summary())
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    def validate_role_integration(self) -> Dict[str, Any]:
        """
        Валидировать интеграцию ролей.
        
        Returns:
            Результаты валидации
        """
        base_errors = self.base_manager.validate_config()
        
        validation_results = {
            "is_valid": len(base_errors) == 0,
            "base_errors": base_errors,
            "integration_checks": {},
            "summary": {}
        }
        
        # Дополнительные проверки интеграции
        all_employees = self.base_manager.get_all_employees()
        
        # Проверка наличия тимлида
        team_lead = self.base_manager.get_team_lead()
        validation_results["integration_checks"]["has_team_lead"] = team_lead is not None
        
        # Проверка сбалансированности ролей
        role_stats = self.base_manager.get_role_statistics()
        validation_results["integration_checks"]["role_balance"] = {
            "has_decision_makers": any(emp.is_decision_maker() for emp in all_employees),
            "has_tech_lead": RoleType.TECH_LEAD.value in role_stats,
            "total_roles": len(role_stats),
            "role_distribution": role_stats
        }
        
        # Проверка активности команды
        activity_stats = self.base_manager.get_activity_statistics()
        high_activity_count = activity_stats.get(ActivityLevel.HIGH.value, 0) + activity_stats.get(ActivityLevel.MEDIUM_HIGH.value, 0)
        validation_results["integration_checks"]["activity_balance"] = {
            "high_activity_count": high_activity_count,
            "total_employees": len(all_employees),
            "activity_ratio": high_activity_count / len(all_employees) if all_employees else 0,
            "activity_distribution": activity_stats
        }
        
        # Сводка
        validation_results["summary"] = {
            "total_employees": len(all_employees),
            "configured_roles": len(self.base_manager.config.roles_mapping) if self.base_manager.config else 0,
            "validation_errors": len(base_errors),
            "integration_score": self._calculate_integration_score(validation_results)
        }
        
        return validation_results
    
    def _calculate_integration_score(self, validation_results: Dict[str, Any]) -> float:
        """Рассчитать оценку качества интеграции."""
        score = 100.0
        
        # Штрафы за ошибки валидации
        score -= len(validation_results["base_errors"]) * 10
        
        # Штрафы за проблемы интеграции
        checks = validation_results["integration_checks"]
        if not checks.get("has_team_lead", True):
            score -= 20
        
        if not checks.get("role_balance", {}).get("has_decision_makers", True):
            score -= 15
        
        if not checks.get("role_balance", {}).get("has_tech_lead", True):
            score -= 10
        
        activity_ratio = checks.get("activity_balance", {}).get("activity_ratio", 1.0)
        if activity_ratio < 0.3:
            score -= 10
        
        return max(0.0, score)
    
    def get_integration_recommendations(self) -> List[str]:
        """
        Получить рекомендации по улучшению интеграции.
        
        Returns:
            Список рекомендаций
        """
        recommendations = []
        
        validation = self.validate_role_integration()
        
        # Рекомендации на основе ошибок валидации
        for error in validation["base_errors"]:
            if "Team lead" in error:
                recommendations.append("Укажите тимлида команды в конфигурации")
            elif "missing" in error.lower():
                recommendations.append("Заполните недостающие данные сотрудников")
        
        # Рекомендации на основе интеграции
        checks = validation["integration_checks"]
        
        if not checks.get("has_team_lead"):
            recommendations.append("Добавьте тимлида для улучшения координации команды")
        
        if not checks.get("role_balance", {}).get("has_decision_makers"):
            recommendations.append("Добавьте сотрудников с правами принятия решений")
        
        if not checks.get("role_balance", {}).get("has_tech_lead"):
            recommendations.append("Добавьте технического лидера для технической экспертизы")
        
        activity_ratio = checks.get("activity_balance", {}).get("activity_ratio", 1.0)
        if activity_ratio < 0.3:
            recommendations.append("Рассмотрите возможность повышения активности ключевых сотрудников")
        
        return recommendations
    
    def reload_with_validation(self) -> Dict[str, Any]:
        """
        Перезагрузить конфигурацию с валидацией.
        
        Returns:
            Результаты перезагрузки и валидации
        """
        try:
            self.base_manager.reload_config()
            self._analysis_contexts.clear()  # Очищаем кэш контекстов
            
            validation_results = self.validate_role_integration()
            
            return {
                "reload_success": True,
                "validation_results": validation_results,
                "recommendations": self.get_integration_recommendations()
            }
            
        except Exception as e:
            return {
                "reload_success": False,
                "error": str(e),
                "validation_results": None,
                "recommendations": []
            }
    
    def get_employee_insights(self, identifier: str) -> Dict[str, Any]:
        """
        Получить инсайты по сотруднику.
        
        Args:
            identifier: Идентификатор сотрудника
            
        Returns:
            Детальная информация о сотруднике с инсайтами
        """
        context = self.get_employee_context(identifier)
        if not context:
            return {"employee_found": False}
        
        employee = context.employee
        all_employees = self.base_manager.get_all_employees()
        
        # Сравнительные метрики
        task_counts = [emp.task_count for emp in all_employees]
        avg_task_count = sum(task_counts) / len(task_counts) if task_counts else 0
        
        insights = {
            "employee_found": True,
            "basic_info": {
                "name": employee.display_name,
                "role": employee.role.value,
                "activity_level": employee.activity_level.value,
                "task_count": employee.task_count
            },
            "position_in_team": {
                "is_team_lead": employee.employee_id == self.base_manager.config.team_structure.team_lead,
                "is_decision_maker": employee.is_decision_maker(),
                "task_count_vs_average": employee.task_count / avg_task_count if avg_task_count > 0 else 1.0,
                "team_influence_level": employee.team_influence
            },
            "capabilities": {
                "primary_skills": employee.skills.primary,
                "secondary_skills": employee.skills.secondary,
                "specializations": employee.specializations,
                "communication_style": employee.communication_style,
                "decision_making_style": employee.decision_making
            },
            "analysis_context": {
                "focus_areas": context.analysis_rules.focus_areas if context.analysis_rules else [],
                "expected_behaviors": context.analysis_rules.expected_behaviors if context.analysis_rules else [],
                "communication_indicators": context.analysis_rules.communication_indicators if context.analysis_rules else []
            },
            "additional_context": context.context_data
        }
        
        return insights
