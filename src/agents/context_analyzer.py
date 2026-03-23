"""
Context Analyzer Agent for MTS MultAgent System

This agent handles text analysis and context extraction:
- Analyzing meeting protocols and text documents
- Extracting key information and entities
- NLP processing for semantic understanding
- Context summarization and key points extraction
- Sentiment analysis and topic modeling
"""

import asyncio
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from collections import Counter
import structlog

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk import FreqDist
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from src.core.base_agent import BaseAgent, AgentResult
from src.core.models import ContextTask, ContextResult, ExtractedEntity, TextSummary

logger = structlog.get_logger()


class ContextAnalyzer(BaseAgent):
    """
    Agent for analyzing text context and extracting key information.
    
    Handles natural language processing, entity extraction,
    and context analysis from meeting protocols and documents.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ContextAnalyzer with configuration.
        
        Args:
            config: Configuration dictionary containing NLP settings
        """
        super().__init__(config, "ContextAnalyzer")
        
        # Validate required configuration
        required_keys = ["context.languages", "context.min_relevance_score"]
        if not self.validate_config(required_keys):
            raise ValueError("Missing required ContextAnalyzer configuration")
        
        self.languages = self.get_config_value("context.languages", ["ru", "en"])
        self.min_relevance_score = self.get_config_value("context.min_relevance_score", 0.3)
        self.max_summary_length = self.get_config_value("context.max_summary_length", 500)
        
        # Initialize NLP models
        self.nlp_models = {}
        self.stop_words = {}
        
        asyncio.create_task(self._initialize_nlp_models())
    
    async def _initialize_nlp_models(self):
        """Initialize NLP models asynchronously."""
        try:
            if SPACY_AVAILABLE:
                # Load spacy models for supported languages
                for lang in self.languages:
                    try:
                        if lang == "ru":
                            self.nlp_models[lang] = spacy.load("ru_core_news_sm")
                        elif lang == "en":
                            self.nlp_models[lang] = spacy.load("en_core_web_sm")
                        self.logger.info(f"Loaded spaCy model for {lang}")
                    except OSError:
                        self.logger.warning(f"spaCy model not available for {lang}")
            
            if NLTK_AVAILABLE:
                # Load NLTK stop words
                for lang in self.languages:
                    try:
                        if lang == "ru":
                            self.stop_words[lang] = set(stopwords.words('russian'))
                        elif lang == "en":
                            self.stop_words[lang] = set(stopwords.words('english'))
                    except OSError:
                        self.logger.warning(f"NLTK stop words not available for {lang}")
                        self.stop_words[lang] = set()
                        
        except Exception as e:
            self.logger.error(f"Failed to initialize NLP models: {str(e)}")
    
    async def validate(self, task: Dict[str, Any]) -> bool:
        """
        Validate ContextAnalyzer task parameters.
        
        Args:
            task: Task dictionary with ContextTask parameters
            
        Returns:
            True if valid, False otherwise
        """
        try:
            context_task = ContextTask(**task)
            
            # Additional validation
            if not context_task.text_content and not context_task.meeting_protocols:
                self.logger.error("Either text_content or meeting_protocols is required")
                return False
            
            if context_task.search_keywords and not isinstance(context_task.search_keywords, list):
                self.logger.error("search_keywords must be a list")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("Context task validation failed", error=str(e))
            return False
    
    async def execute(self, task: Dict[str, Any]) -> AgentResult:
        """
        Execute context analysis task.
        
        Args:
            task: Task dictionary containing context analysis parameters
            
        Returns:
            AgentResult with analyzed context
        """
        context_task = ContextTask(**task)
        
        try:
            # Combine all text sources
            all_text = self._combine_text_sources(context_task)
            
            if not all_text.strip():
                raise ValueError("No text content to analyze")
            
            # Detect language
            detected_language = await self._detect_language(all_text)
            
            # Extract entities
            entities = await self._extract_entities(all_text, detected_language)
            
            # Extract key phrases
            key_phrases = await self._extract_key_phrases(all_text, detected_language)
            
            # Find relevant context based on keywords
            relevant_context = await self._find_relevant_context(
                all_text, 
                context_task.search_keywords, 
                detected_language
            )
            
            # Generate summary
            summary = await self._generate_summary(all_text, detected_language)
            
            # Calculate relevance scores
            relevance_scores = await self._calculate_relevance_scores(
                all_text,
                context_task.search_keywords,
                detected_language
            )
            
            # Create result
            result = ContextResult(
                entities=entities,
                key_phrases=key_phrases,
                relevant_context=relevant_context,
                summary=summary,
                language=detected_language,
                relevance_scores=relevance_scores,
                analysis_timestamp=datetime.now(),
                metadata={
                    "text_length": len(all_text),
                    "nlp_tools_used": self._get_available_tools(),
                    "processing_time": datetime.now().isoformat()
                }
            )
            
            self.logger.info(
                "Context analysis completed",
                entities=len(entities),
                key_phrases=len(key_phrases),
                language=detected_language
            )
            
            return AgentResult(
                success=True,
                data=result.dict(),
                agent_name=self.name
            )
            
        except Exception as e:
            self.logger.error("Context analysis failed", error=str(e), exc_info=True)
            return AgentResult(
                success=False,
                error=f"Context analysis failed: {str(e)}",
                agent_name=self.name
            )
    
    def _combine_text_sources(self, task: ContextTask) -> str:
        """
        Combine text from various sources.
        
        Args:
            task: ContextTask with text sources
            
        Returns:
            Combined text string
        """
        text_parts = []
        
        # Add main text content
        if task.text_content:
            text_parts.append(task.text_content)
        
        # Add meeting protocols
        if task.meeting_protocols:
            for protocol in task.meeting_protocols:
                if isinstance(protocol, dict):
                    # Handle protocol object
                    content = protocol.get("content", "")
                    title = protocol.get("title", "")
                    if title and content:
                        text_parts.append(f"## {title}\n{content}")
                    elif content:
                        text_parts.append(content)
                else:
                    # Handle string protocol
                    text_parts.append(str(protocol))
        
        # Add additional documents
        if task.additional_documents:
            for doc in task.additional_documents:
                if isinstance(doc, dict):
                    content = doc.get("content", "")
                    if content:
                        text_parts.append(content)
                else:
                    text_parts.append(str(doc))
        
        return "\n\n".join(text_parts)
    
    async def _detect_language(self, text: str) -> str:
        """
        Detect the language of the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (e.g., 'ru', 'en')
        """
        # Simple language detection based on character patterns
        russian_chars = len(re.findall(r'[а-яё]', text.lower()))
        english_chars = len(re.findall(r'[a-z]', text.lower()))
        total_chars = russian_chars + english_chars
        
        if total_chars == 0:
            return "en"  # Default to English
        
        russian_ratio = russian_chars / total_chars
        
        if russian_ratio > 0.3:
            return "ru"
        else:
            return "en"
    
    async def _extract_entities(self, text: str, language: str) -> List[ExtractedEntity]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        try:
            # Use spaCy if available
            if SPACY_AVAILABLE and language in self.nlp_models:
                doc = self.nlp_models[language](text)
                
                for ent in doc.ents:
                    entity = ExtractedEntity(
                        text=ent.text,
                        label=ent.label_,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=1.0,  # spaCy doesn't provide confidence by default
                        context=text[max(0, ent.start_char-50):ent.end_char+50]
                    )
                    entities.append(entity)
            
            # Fallback to regex-based extraction
            if not entities:
                entities = await self._extract_entities_regex(text)
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {str(e)}")
            # Fallback to simple extraction
            entities = await self._extract_entities_regex(text)
        
        return entities
    
    async def _extract_entities_regex(self, text: str) -> List[ExtractedEntity]:
        """
        Extract entities using regex patterns (fallback method).
        
        Args:
            text: Text to analyze
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Common patterns for Russian and English
        patterns = {
            "PERSON": r'\b([А-Я][а-я]+ [А-Я][а-я]+(?: [А-Я][а-я]+)?)\b|\b([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?)\b',
            "ORG": r'\b([А-Я][а-я]+ [А-Я][а-я]+\s*(?:ООО|АО|ЗАО|ОАО|ИП|Ltd|Inc|Corp|LLC))\b',
            "DATE": r'\b(\d{1,2}\.\d{1,2}\.\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4})\b',
            "PHONE": r'\b(\+?\d{1,3}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})\b',
            "EMAIL": r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b'
        }
        
        for label, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entity = ExtractedEntity(
                    text=match.group(),
                    label=label,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.7,  # Lower confidence for regex-based extraction
                    context=text[max(0, match.start()-30):match.end()+30]
                )
                entities.append(entity)
        
        return entities
    
    async def _extract_key_phrases(self, text: str, language: str) -> List[str]:
        """
        Extract key phrases from text.
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of key phrases
        """
        try:
            # Use NLTK if available
            if NLTK_AVAILABLE:
                return await self._extract_key_phrases_nltk(text, language)
            else:
                return await self._extract_key_phrases_simple(text, language)
                
        except Exception as e:
            self.logger.error(f"Key phrase extraction failed: {str(e)}")
            return await self._extract_key_phrases_simple(text, language)
    
    async def _extract_key_phrases_nltk(self, text: str, language: str) -> List[str]:
        """Extract key phrases using NLTK."""
        # Tokenize and filter stop words
        tokens = word_tokenize(text.lower(), language=language)
        stop_words = self.stop_words.get(language, set())
        
        # Filter tokens
        filtered_tokens = [
            token for token in tokens 
            if token.isalpha() and len(token) > 2 and token not in stop_words
        ]
        
        # Calculate frequency distribution
        freq_dist = FreqDist(filtered_tokens)
        
        # Extract most common words
        common_words = [word for word, count in freq_dist.most_common(20)]
        
        # Generate key phrases (2-3 word combinations)
        key_phrases = []
        sentences = sent_tokenize(text, language=language)
        
        for sentence in sentences:
            words = word_tokenize(sentence.lower(), language=language)
            for i in range(len(words) - 1):
                # Check 2-word phrases
                if words[i] in common_words and words[i+1] in common_words:
                    phrase = f"{words[i]} {words[i+1]}"
                    if phrase not in key_phrases:
                        key_phrases.append(phrase)
                
                # Check 3-word phrases
                if i < len(words) - 2:
                    if (words[i] in common_words and 
                        words[i+1] in common_words and 
                        words[i+2] in common_words):
                        phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                        if phrase not in key_phrases:
                            key_phrases.append(phrase)
        
        return key_phrases[:15]  # Return top 15 phrases
    
    async def _extract_key_phrases_simple(self, text: str, language: str) -> List[str]:
        """Extract key phrases using simple methods."""
        # Split into words and filter
        words = re.findall(r'\b[a-zA-Zа-яёА-ЯЁ]{3,}\b', text.lower())
        
        # Count word frequencies
        word_freq = Counter(words)
        common_words = [word for word, count in word_freq.most_common(20)]
        
        # Find phrases containing common words
        key_phrases = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence_words = re.findall(r'\b[a-zA-Zа-яёА-ЯЁ]{3,}\b', sentence.lower())
            for i in range(len(sentence_words) - 1):
                if (sentence_words[i] in common_words and 
                    sentence_words[i+1] in common_words):
                    phrase = f"{sentence_words[i]} {sentence_words[i+1]}"
                    if phrase not in key_phrases:
                        key_phrases.append(phrase)
        
        return key_phrases[:15]
    
    async def _find_relevant_context(
        self, 
        text: str, 
        keywords: Optional[List[str]], 
        language: str
    ) -> List[str]:
        """
        Find relevant text sections based on keywords.
        
        Args:
            text: Text to search in
            keywords: List of keywords to search for
            language: Language code
            
        Returns:
            List of relevant text sections
        """
        if not keywords:
            return []
        
        relevant_sections = []
        sentences = re.split(r'[.!?]+', text)
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            for sentence in sentences:
                if keyword_lower in sentence.lower():
                    # Add surrounding sentences for context
                    sentence_index = sentences.index(sentence)
                    start_idx = max(0, sentence_index - 1)
                    end_idx = min(len(sentences), sentence_index + 2)
                    
                    context_section = '. '.join(sentences[start_idx:end_idx]).strip()
                    if context_section and context_section not in relevant_sections:
                        relevant_sections.append(context_section)
        
        return relevant_sections[:10]  # Return top 10 relevant sections
    
    async def _generate_summary(self, text: str, language: str) -> TextSummary:
        """
        Generate a summary of the text.
        
        Args:
            text: Text to summarize
            language: Language code
            
        Returns:
            TextSummary object
        """
        try:
            # Extract sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return TextSummary(
                    summary="",
                    bullet_points=[],
                    key_topics=[],
                    word_count=0
                )
            
            # Simple extractive summarization
            # Score sentences based on length and keyword frequency
            scored_sentences = []
            
            for i, sentence in enumerate(sentences):
                # Score based on position, length, and keyword prominence
                position_score = 1.0 - (i / len(sentences))  # Earlier sentences get higher scores
                length_score = min(len(sentence.split()) / 20, 1.0)  # Prefer medium-length sentences
                
                # Count common words
                words = sentence.lower().split()
                word_freq = Counter(words)
                content_score = sum(word_freq[word] for word in word_freq if len(word) > 3) / len(words) if words else 0
                
                total_score = position_score * 0.3 + length_score * 0.3 + content_score * 0.4
                scored_sentences.append((sentence, total_score))
            
            # Sort by score and select top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            top_sentences = [s[0] for s in scored_sentences[:5]]
            
            # Generate summary
            summary = '. '.join(top_sentences[:3])  # Top 3 sentences for summary
            if len(summary) > self.max_summary_length:
                summary = summary[:self.max_summary_length] + "..."
            
            # Generate bullet points from key sentences
            bullet_points = [f"• {s}" for s in top_sentences[:5]]
            
            # Extract key topics
            key_phrases = await self._extract_key_phrases(text, language)
            key_topics = key_phrases[:10]
            
            return TextSummary(
                summary=summary,
                bullet_points=bullet_points,
                key_topics=key_topics,
                word_count=len(text.split())
            )
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {str(e)}")
            return TextSummary(
                summary="Summary generation failed",
                bullet_points=[],
                key_topics=[],
                word_count=len(text.split())
            )
    
    async def _calculate_relevance_scores(
        self, 
        text: str, 
        keywords: Optional[List[str]], 
        language: str
    ) -> Dict[str, float]:
        """
        Calculate relevance scores for keywords.
        
        Args:
            text: Text to analyze
            keywords: List of keywords to score
            language: Language code
            
        Returns:
            Dictionary with keyword relevance scores
        """
        scores = {}
        
        if not keywords:
            return scores
        
        text_lower = text.lower()
        total_words = len(text_lower.split())
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Count keyword occurrences
            exact_matches = text_lower.count(keyword_lower)
            
            # Calculate relevance score based on frequency
            if total_words > 0:
                frequency_score = exact_matches / total_words
            else:
                frequency_score = 0
            
            # Boost score based on keyword prominence (appears in titles, first sentences)
            prominence_score = 0
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if keyword_lower in line.lower():
                    if i == 0:  # First line (likely title)
                        prominence_score += 0.3
                    elif i < 3:  # First few lines
                        prominence_score += 0.1
            
            # Combine scores
            final_score = (frequency_score * 0.7) + (prominence_score * 0.3)
            scores[keyword] = round(final_score, 4)
        
        return scores
    
    def _get_available_tools(self) -> List[str]:
        """
        Get list of available NLP tools.
        
        Returns:
            List of available tool names
        """
        tools = []
        if SPACY_AVAILABLE:
            tools.append("spacy")
        if NLTK_AVAILABLE:
            tools.append("nltk")
        tools.append("regex")  # Always available
        
        return tools
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for ContextAnalyzer agent.
        
        Returns:
            Health check result
        """
        base_health = await super().health_check()
        
        try:
            # Test NLP functionality
            test_text = "This is a test text for processing."
            test_result = await self._detect_language(test_text)
            nlp_health = {"status": "healthy", "language_detection": True}
        except Exception as e:
            nlp_health = {"status": "error", "language_detection": False, "error": str(e)}
        
        base_health.update({
            "context_configured": bool(self.languages),
            "nlp_tools_available": self._get_available_tools(),
            "spacy_available": SPACY_AVAILABLE,
            "nltk_available": NLTK_AVAILABLE,
            "supported_languages": self.languages,
            "nlp_health": nlp_health
        })
        
        return base_health
