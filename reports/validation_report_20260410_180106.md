
# Employee Monitoring System - Configuration Validation Report

**Generated:** 2026-04-10T18:01:06.754456
**Total Checks:** 36
**Passed:** 20
**Failed:** 13
**Warnings:** 3

## Summary Status: ❌ NEEDS ATTENTION

## Detailed Results

### ENV

- ❌ **ENV: JIRA_BASE_URL**: Required environment variable JIRA_BASE_URL is missing

- ❌ **ENV: JIRA_USERNAME**: Required environment variable JIRA_USERNAME is missing

- ❌ **ENV: JIRA_ACCESS_TOKEN**: Required environment variable JIRA_ACCESS_TOKEN is missing

- ❌ **ENV: JIRA_PROJECT_KEYS**: Required environment variable JIRA_PROJECT_KEYS is missing

- ❌ **ENV: LLM_API_KEY**: Required environment variable LLM_API_KEY is missing

- ❌ **ENV: LLM_API_BASE_URL**: Required environment variable LLM_API_BASE_URL is missing

- ❌ **ENV: LLM_MODEL**: Required environment variable LLM_MODEL is missing

- ❌ **ENV: CONFLUENCE_BASE_URL**: Required environment variable CONFLUENCE_BASE_URL is missing

- ❌ **ENV: CONFLUENCE_ACCESS_TOKEN**: Required environment variable CONFLUENCE_ACCESS_TOKEN is missing

- ❌ **ENV: CONFLUENCE_PARENT_PAGE_ID**: Required environment variable CONFLUENCE_PARENT_PAGE_ID is missing

- ❌ **ENV: DAILY_REPORTS_DIR**: Required environment variable DAILY_REPORTS_DIR is missing

- ❌ **ENV: WEEKLY_REPORTS_DIR**: Required environment variable WEEKLY_REPORTS_DIR is missing

- ❌ **ENV: PROTOCOLS_DIRECTORY_PATH**: Required environment variable PROTOCOLS_DIRECTORY_PATH is missing

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

- ⚠️ **API: LLM_API**: API LLM_API test failed: Invalid URL 'None': No scheme supplied. Perhaps you meant https://None?

- ⚠️ **API: JIRA_API**: API JIRA_API test failed: Invalid URL 'None': No scheme supplied. Perhaps you meant https://None?

- ⚠️ **API: CONFLUENCE_API**: API CONFLUENCE_API test failed: Invalid URL 'None': No scheme supplied. Perhaps you meant https://None?

## Recommendations

1. Fix all FAILED items before proceeding with development
2. Address WARNING items to improve system reliability
3. Re-run validation after making changes
