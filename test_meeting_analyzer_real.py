#!/usr/bin/env python3
"""
Тестирование Meeting Analyzer Agent с реальными протоколами собраний
"""

import asyncio
import sys
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
sys.path.append('src')

from agents.meeting_analyzer_agent_full import MeetingAnalyzerAgentFull
from core.config_manager import ConfigurationManager
from core.base_agent import AgentConfig

