"""
Модели ролей и командной структуры для системы анализа сотрудников.

Этот модуль определяет классы для работы с ролями сотрудников,
командной структурой и контекстом анализа на основе конфигурации roles.yaml.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum
import yaml
from pathlib import Path


class ActivityLevel(Enum):
    """Уровни активности сотрудников."""
    HIGH = "high"
    MEDIUM_HIGH = "medium_high"
    MEDIUM = "medium"
    LOW = "low"


class RoleType(Enum):
    """Типы ролей в команде."""
    TECH_LEAD = "tech_lead"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    PRODUCT_OWNER = "product_owner"
    ANALYST = "analyst"


class DecisionAuthority(Enum):
    """Уровень полномочий принятия решений."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EmployeeSkills:
    """Навыки сотрудника."""
    primary: List[str] = field(default_factory=list)
    secondary: List[str] = field(default_factory=list)
    
    def get_all_skills(self) -> Set[str]:
        """Получить все навыки сотрудника."""
        return set(self.primary + self.secondary)
    
    def has_skill(self, skill: str) -> bool:
        """Проверить наличие навыка."""
        return skill in self.primary or skill in self.secondary


@dataclass
class EmployeeProfile:
    """Полный профиль сотрудника."""
    # Идентификация
    employee_id: str  # internal key (болотин_андрей)
    full_name: str
    display_name: str
    jira_name: str
    email: str
    
    # Роль и активность
    role: RoleType
    activity_level: ActivityLevel
    task_count: int = 0
    team_influence: str = "medium"
    
    # Профессиональные характеристики
    skills: EmployeeSkills = field(default_factory=EmployeeSkills)
    specializations: List[str] = field(default_factory=list)
    communication_style: str = ""
    decision_making: str = ""
    
    # Дополнительные данные
    product: Optional[str] = None
    
    def is_high_activity(self) -> bool:
        """Проверить высокую активность."""
        return self.activity_level in [ActivityLevel.HIGH, ActivityLevel.MEDIUM_HIGH]
    
    def is_decision_maker(self) -> bool:
        """Проверить право принятия решений."""
        return self.role in [RoleType.TECH_LEAD, RoleType.PRODUCT_OWNER]
    
    def get_focus_areas(self, role_config: Dict[str, Any]) -> List[str]:
        """Получить фокусные области для роли."""
        role_key = self.role.value
        if role_key in role_config:
            return role_config[role_key].get("focus_areas", [])
        return []


@dataclass
class RoleDefinition:
    """Определение роли."""
    role_type: RoleType
    description: str
    responsibilities: List[str]
    decision_authority: DecisionAuthority
    focus_areas: List[str]
    
    def has_authority(self, level: DecisionAuthority) -> bool:
        """Проверить уровень полномочий."""
        authority_order = {
            DecisionAuthority.HIGH: 3,
            DecisionAuthority.MEDIUM: 2,
            DecisionAuthority.LOW: 1
        }
        return authority_order[self.decision_authority] >= authority_order[level]


@dataclass
class AnalysisRules:
    """Правила анализа для ролей."""
    focus_areas: List[str]
    expected_behaviors: List[str]
    communication_indicators: List[str]


@dataclass
class TeamStructure:
    """Структура команды."""
    name: str
    project: str
    department: str
    team_lead: str
    total_employees: int = 0
    active_employees: int = 0
    unassigned_percentage: float = 0.0


@dataclass
class RoleContextConfig:
    """Конфигурация контекстной системы ролей."""
    metadata: Dict[str, Any] = field(default_factory=dict)
    team_structure: TeamStructure = field(default_factory=lambda: TeamStructure("", "", "", ""))
    analysis_settings: Dict[str, Any] = field(default_factory=dict)
    roles_mapping: Dict[RoleType, RoleDefinition] = field(default_factory=dict)
    employees: Dict[str, EmployeeProfile] = field(default_factory=dict)
    analysis_rules: Dict[RoleType, AnalysisRules] = field(default_factory=dict)
    name_mapping: Dict[str, str] = field(default_factory=dict)
    
    def get_employee_by_jira_name(self, jira_name: str) -> Optional[EmployeeProfile]:
        """Получить сотрудника по Jira имени."""
        for employee in self.employees.values():
            if employee.jira_name == jira_name:
                return employee
        return None
    
    def get_employee_by_display_name(self, display_name: str) -> Optional[EmployeeProfile]:
        """Получить сотрудника по отображаемому имени."""
        for employee in self.employees.values():
            if employee.display_name == display_name:
                return employee
        return None
    
    def get_employees_by_role(self, role: RoleType) -> List[EmployeeProfile]:
        """Получить сотрудников по роли."""
        return [emp for emp in self.employees.values() if emp.role == role]
    
    def get_high_activity_employees(self) -> List[EmployeeProfile]:
        """Получить высокоактивных сотрудников."""
        return [emp for emp in self.employees.values() if emp.is_high_activity()]
    
    def get_decision_makers(self) -> List[EmployeeProfile]:
        """Получить сотрудников с правом принятия решений."""
        return [emp for emp in self.employees.values() if emp.is_decision_maker()]
    
    def get_team_lead(self) -> Optional[EmployeeProfile]:
        """Получить тимлида команды."""
        return self.employees.get(self.team_structure.team_lead)


class RoleContextManager:
    """Менеджер контекста ролей."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Инициализация менеджера контекста ролей.
        
        Args:
            config_path: Путь к файлу конфигурации roles.yaml
        """
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "roles.yaml"
        self.config: Optional[RoleContextConfig] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Загрузить конфигурацию из YAML файла."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
            
            self.config = self._parse_config(data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    def _parse_config(self, data: Dict[str, Any]) -> RoleContextConfig:
        """Распарсить конфигурацию из словаря."""
        config = RoleContextConfig()
        
        # Метаданные
        config.metadata = data.get("metadata", {})
        
        # Структура команды
        team_data = data.get("team_structure", {})
        config.team_structure = TeamStructure(
            name=team_data.get("name", ""),
            project=team_data.get("project", ""),
            department=team_data.get("department", ""),
            team_lead=team_data.get("team_lead", ""),
            total_employees=config.metadata.get("total_employees", 0),
            active_employees=config.metadata.get("active_employees", 0),
            unassigned_percentage=config.metadata.get("unassigned_percentage", 0.0)
        )
        
        # Настройки анализа
        config.analysis_settings = data.get("analysis_settings", {})
        
        # Маппинг ролей
        roles_data = data.get("roles_mapping", {})
        for role_key, role_info in roles_data.items():
            try:
                role_type = RoleType(role_key)
                config.roles_mapping[role_type] = RoleDefinition(
                    role_type=role_type,
                    description=role_info.get("description", ""),
                    responsibilities=role_info.get("responsibilities", []),
                    decision_authority=DecisionAuthority(role_info.get("decision_authority", "medium")),
                    focus_areas=role_info.get("focus_areas", [])
                )
            except ValueError:
                # Пропускаем неизвестные роли
                continue
        
        # Профили сотрудников
        employees_data = data.get("employees", {})
        for emp_id, emp_info in employees_data.items():
            try:
                role_type = RoleType(emp_info.get("role", "analyst"))
                config.employees[emp_id] = EmployeeProfile(
                    employee_id=emp_id,
                    full_name=emp_info.get("full_name", ""),
                    display_name=emp_info.get("display_name", ""),
                    jira_name=emp_info.get("jira_name", ""),
                    email=emp_info.get("email", ""),
                    role=role_type,
                    activity_level=ActivityLevel(emp_info.get("activity_level", "medium")),
                    task_count=emp_info.get("task_count", 0),
                    team_influence=emp_info.get("team_influence", "medium"),
                    skills=EmployeeSkills(
                        primary=emp_info.get("skills", {}).get("primary", []),
                        secondary=emp_info.get("skills", {}).get("secondary", [])
                    ),
                    specializations=emp_info.get("specializations", []),
                    communication_style=emp_info.get("communication_style", ""),
                    decision_making=emp_info.get("decision_making", ""),
                    product=emp_info.get("product")
                )
            except ValueError:
                # Пропускаем с неверными данными
                continue
        
        # Правила анализа
        analysis_rules_data = data.get("analysis_rules", {})
        for role_key, rules_info in analysis_rules_data.items():
            try:
                role_type = RoleType(role_key)
                config.analysis_rules[role_type] = AnalysisRules(
                    focus_areas=rules_info.get("focus_areas", []),
                    expected_behaviors=rules_info.get("expected_behaviors", []),
                    communication_indicators=rules_info.get("communication_indicators", [])
                )
            except ValueError:
                # Пропускаем неизвестные роли
                continue
        
        # Маппинг имен
        config.name_mapping = data.get("name_mapping", {})
        
        return config
    
    def get_employee(self, identifier: str) -> Optional[EmployeeProfile]:
        """
        Получить сотрудника по любому идентификатору.
        
        Args:
            identifier: ID, Jira имя или отображаемое имя
            
        Returns:
            Профиль сотрудника или None если не найден
        """
        if not self.config:
            return None
        
        # Пробуем internal ID
        if identifier in self.config.employees:
            return self.config.employees[identifier]
        
        # Пробуем Jira имя
        employee = self.config.get_employee_by_jira_name(identifier)
        if employee:
            return employee
        
        # Пробуем отображаемое имя
        employee = self.config.get_employee_by_display_name(identifier)
        if employee:
            return employee
        
        # Пробуем маппинг имен
        if identifier in self.config.name_mapping:
            mapped_id = self.config.name_mapping[identifier]
            return self.config.employees.get(mapped_id)
        
        return None
    
    def get_employees_by_activity(self, activity_level: ActivityLevel) -> List[EmployeeProfile]:
        """Получить сотрудников по уровню активности."""
        if not self.config:
            return []
        return [emp for emp in self.config.employees.values() if emp.activity_level == activity_level]
    
    def get_role_definition(self, role_type: RoleType) -> Optional[RoleDefinition]:
        """Получить определение роли."""
        if not self.config:
            return None
        return self.config.roles_mapping.get(role_type)
    
    def get_analysis_rules(self, role_type: RoleType) -> Optional[AnalysisRules]:
        """Получить правила анализа для роли."""
        if not self.config:
            return None
        return self.config.analysis_rules.get(role_type)
    
    def get_team_structure(self) -> Optional[TeamStructure]:
        """Получить структуру команды."""
        if not self.config:
            return None
        return self.config.team_structure
    
    def get_all_employees(self) -> List[EmployeeProfile]:
        """Получить всех сотрудников."""
        if not self.config:
            return []
        return list(self.config.employees.values())
    
    def validate_config(self) -> List[str]:
        """
        Валидировать конфигурацию.
        
        Returns:
            Список ошибок валидации
        """
        errors = []
        
        if not self.config:
            errors.append("Configuration not loaded")
            return errors
        
        # Проверка структуры команды
        if not self.config.team_structure.team_lead:
            errors.append("Team lead not specified")
        
        if self.config.team_structure.team_lead not in self.config.employees:
            errors.append(f"Team lead {self.config.team_structure.team_lead} not found in employees")
        
        # Проверка сотрудников
        for emp_id, employee in self.config.employees.items():
            if not employee.full_name:
                errors.append(f"Employee {emp_id} missing full name")
            
            if not employee.jira_name:
                errors.append(f"Employee {emp_id} missing Jira name")
            
            if not employee.email:
                errors.append(f"Employee {emp_id} missing email")
        
        # Проверка маппинга имен
        for jira_name, internal_id in self.config.name_mapping.items():
            if internal_id not in self.config.employees:
                errors.append(f"Name mapping {jira_name} -> {internal_id} points to non-existent employee")
        
        return errors
    
    def reload_config(self) -> None:
        """Перезагрузить конфигурацию."""
        self._load_config()
    
    def get_role_statistics(self) -> Dict[str, int]:
        """Получить статистику по ролям."""
        if not self.config:
            return {}
        
        stats = {}
        for employee in self.config.employees.values():
            role_name = employee.role.value
            stats[role_name] = stats.get(role_name, 0) + 1
        
        return stats
    
    def get_activity_statistics(self) -> Dict[str, int]:
        """Получить статистику по активности."""
        if not self.config:
            return {}
        
        stats = {}
        for employee in self.config.employees.values():
            activity = employee.activity_level.value
            stats[activity] = stats.get(activity, 0) + 1
        
        return stats
    
    def get_decision_makers(self) -> List[EmployeeProfile]:
        """Получить сотрудников с правом принятия решений."""
        if not self.config:
            return []
        return [emp for emp in self.config.employees.values() if emp.is_decision_maker()]
    
    def get_high_activity_employees(self) -> List[EmployeeProfile]:
        """Получить высокоактивных сотрудников."""
        if not self.config:
            return []
        return [emp for emp in self.config.employees.values() if emp.is_high_activity()]
    
    def get_team_lead(self) -> Optional[EmployeeProfile]:
        """Получить тимлида команды."""
        if not self.config:
            return None
        return self.config.employees.get(self.config.team_structure.team_lead)
