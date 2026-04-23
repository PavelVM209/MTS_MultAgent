
# Employee Monitoring System - Configuration Validation Report

**Generated:** 2026-04-23T02:50:28.015607
**Total Checks:** 36
**Passed:** 35
**Failed:** 0
**Warnings:** 1

## Summary Status: ✅ HEALTHY

## Detailed Results

### ENV

- ✅ **ENV: JIRA_BASE_URL**: Environment variable JIRA_BASE_URL is set
  - value: https://jira.mts.ru

- ✅ **ENV: JIRA_USERNAME**: Environment variable JIRA_USERNAME is set
  - value: sa0000openbdrnd

- ✅ **ENV: JIRA_ACCESS_TOKEN**: Environment variable JIRA_ACCESS_TOKEN is set
  - value: NDg0NDQ2ODIwNzA0Onj7dh98baq+jI5A6wvKRbCWvgDJ

- ✅ **ENV: JIRA_PROJECT_KEYS**: Environment variable JIRA_PROJECT_KEYS is set
  - value: OPENBD

- ✅ **ENV: LLM_API_KEY**: Environment variable LLM_API_KEY is set
  - value: 5dc1fddb-4c05-4b89-990d-0df4ce923fe0

- ✅ **ENV: LLM_API_BASE_URL**: Environment variable LLM_API_BASE_URL is set
  - value: https://devx-copilot.tech/v1

- ✅ **ENV: LLM_MODEL**: Environment variable LLM_MODEL is set
  - value: glm-4.6-357b

- ✅ **ENV: CONFLUENCE_BASE_URL**: Environment variable CONFLUENCE_BASE_URL is set
  - value: https://confluence.mts.ru

- ✅ **ENV: CONFLUENCE_ACCESS_TOKEN**: Environment variable CONFLUENCE_ACCESS_TOKEN is set
  - value: NzQyNDUwNjc1NzA1Ouw+Vm88RWD9qzDbhKoSB9CA9v/a

- ✅ **ENV: CONFLUENCE_PARENT_PAGE_ID**: Environment variable CONFLUENCE_PARENT_PAGE_ID is set
  - value: 2294163264

- ✅ **ENV: DAILY_REPORTS_DIR**: Environment variable DAILY_REPORTS_DIR is set
  - value: reports/daily

- ✅ **ENV: WEEKLY_REPORTS_DIR**: Environment variable WEEKLY_REPORTS_DIR is set
  - value: reports/weekly

- ✅ **ENV: PROTOCOLS_DIRECTORY_PATH**: Environment variable PROTOCOLS_DIRECTORY_PATH is set
  - value: protocols

### CONFIG

- ✅ **CONFIG: config/employee_monitoring.yaml**: Configuration file config/employee_monitoring.yaml has valid structure
  - sections: ['employee_monitoring', 'development']

- ✅ **CONFIG: config/base.yaml**: Configuration file config/base.yaml is valid YAML

- ✅ **CONFIG: config/development.yaml**: Configuration file config/development.yaml is valid YAML

- ✅ **CONFIG: config/production.yaml**: Configuration file config/production.yaml is valid YAML

### DIRECTORY

- ✅ **DIRECTORY: protocols**: Directory protocols exists

- ✅ **DIRECTORY: reports/daily**: Directory reports/daily exists

- ✅ **DIRECTORY: reports/weekly**: Directory reports/weekly exists

- ✅ **DIRECTORY: reports/quality**: Directory reports/quality exists

- ✅ **DIRECTORY: data/memory**: Directory data/memory exists

- ✅ **DIRECTORY: src/agents**: Directory src/agents exists

- ✅ **DIRECTORY: src/core**: Directory src/core exists

- ✅ **DIRECTORY: tests**: Directory tests exists

### MODULE

- ✅ **MODULE: yaml**: Module yaml is available

- ✅ **MODULE: requests**: Module requests is available

- ✅ **MODULE: asyncio**: Module asyncio is available

- ✅ **MODULE: pydantic**: Module pydantic is available

- ✅ **MODULE: dotenv**: Module dotenv is available

- ✅ **MODULE: pathlib**: Module pathlib is available

- ✅ **MODULE: logging**: Module logging is available

- ✅ **MODULE: datetime**: Module datetime is available

### API

- ⚠️ **API: LLM_API**: API LLM_API returned unexpected status: 404

- ✅ **API: JIRA_API**: API JIRA_API is reachable
  - status_code: 401
  - url: https://jira.mts.ru

- ✅ **API: CONFLUENCE_API**: API CONFLUENCE_API is reachable
  - status_code: 200
  - url: https://confluence.mts.ru

