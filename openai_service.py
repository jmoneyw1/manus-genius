import asyncio
import openai
import logging
import json
import time
from typing import Dict, List, Optional, AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from config import Config

logger = logging.getLogger(__name__)

class OpenAIService:
    """Enhanced OpenAI service with async support and streaming"""
    
    def __init__(self):
        self.config = Config
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        if not self.config.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured - using simulation mode")
            return
        
        try:
            openai.api_key = self.config.OPENAI_API_KEY
            self.client = openai
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
    
    async def analyze_code_async(self, task_description: str, project_structure: Dict) -> Dict:
        """Analyze code asynchronously"""
        try:
            if not self.client:
                return self._simulate_analysis(task_description, project_structure)
            
            # Run OpenAI call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._analyze_code_sync,
                task_description,
                project_structure
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in async code analysis: {str(e)}")
            return self._create_error_response(str(e))
    
    def _analyze_code_sync(self, task_description: str, project_structure: Dict) -> Dict:
        """Synchronous OpenAI analysis"""
        try:
            # Prepare context from project structure
            context = self._prepare_context(project_structure)
            
            # Create system prompt
            system_prompt = self._create_system_prompt()
            
            # Create user prompt
            user_prompt = self._create_user_prompt(task_description, context)
            
            # Make OpenAI API call
            response = self.client.ChatCompletion.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=self.config.OPENAI_TEMPERATURE,
                timeout=30
            )
            
            # Parse response
            content = response.choices[0].message.content
            return self._parse_openai_response(content)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return self._create_error_response(f"OpenAI API error: {str(e)}")
    
    async def stream_analysis(self, task_description: str, project_structure: Dict) -> AsyncGenerator[str, None]:
        """Stream OpenAI response for real-time updates"""
        try:
            if not self.client:
                async for chunk in self._simulate_streaming(task_description, project_structure):
                    yield chunk
                return
            
            # Prepare context
            context = self._prepare_context(project_structure)
            system_prompt = self._create_system_prompt()
            user_prompt = self._create_user_prompt(task_description, context)
            
            # Stream OpenAI response
            response = self.client.ChatCompletion.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=self.config.OPENAI_TEMPERATURE,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.get('content'):
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in streaming analysis: {str(e)}")
            yield f"Error: {str(e)}"
    
    def _prepare_context(self, project_structure: Dict) -> str:
        """Prepare project context for OpenAI"""
        context_parts = []
        
        # Project overview
        context_parts.append(f"Project Overview:")
        context_parts.append(f"- Total files: {project_structure.get('total_files', 0)}")
        context_parts.append(f"- Total size: {project_structure.get('total_size', 0)} bytes")
        
        # File categories
        categories = project_structure.get('file_categories', {})
        if categories:
            context_parts.append(f"- File categories: {', '.join(f'{k}: {v}' for k, v in categories.items())}")
        
        # Code files
        code_files = project_structure.get('code_files', [])
        if code_files:
            context_parts.append(f"\nCode Files ({len(code_files)}):")
            for file_info in code_files[:10]:  # Limit to first 10
                context_parts.append(f"- {file_info['path']} ({file_info['formatted_size']})")
        
        # File contents (limited)
        content = project_structure.get('content', {})
        if content:
            context_parts.append(f"\nFile Contents (sample):")
            for file_path, file_content in list(content.items())[:5]:  # Limit to 5 files
                context_parts.append(f"\n--- {file_path} ---")
                # Truncate content if too long
                if len(file_content) > 2000:
                    context_parts.append(file_content[:2000] + "... [truncated]")
                else:
                    context_parts.append(file_content)
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for OpenAI"""
        return """You are Manus AI, an expert code analyst and software engineer. Your role is to:

1. Analyze code projects and provide actionable insights
2. Identify bugs, security issues, and performance problems
3. Suggest improvements and best practices
4. Provide specific code examples and solutions
5. Explain complex concepts clearly

When analyzing code:
- Focus on the specific task requested by the user
- Provide concrete, actionable recommendations
- Include code examples when helpful
- Consider security, performance, and maintainability
- Be thorough but concise

Format your response as JSON with these fields:
{
  "analysis": {
    "task_type": "string",
    "main_language": "string", 
    "complexity": "low|medium|high",
    "files_analyzed": number,
    "estimated_time": "string"
  },
  "summary": "Brief overview of findings",
  "recommendations": ["list", "of", "recommendations"],
  "code_changes": [
    {
      "file": "filename",
      "type": "modification|addition|deletion",
      "description": "what to change",
      "code": "example code",
      "line_numbers": "optional line range"
    }
  ],
  "security_issues": ["list", "of", "security", "concerns"],
  "performance_issues": ["list", "of", "performance", "issues"],
  "next_steps": ["suggested", "next", "actions"]
}"""
    
    def _create_user_prompt(self, task_description: str, context: str) -> str:
        """Create user prompt for OpenAI"""
        return f"""Please analyze this code project and help with the following task:

TASK: {task_description}

PROJECT CONTEXT:
{context}

Please provide a comprehensive analysis focusing on the specific task requested. Include actionable recommendations and code examples where appropriate."""
    
    def _parse_openai_response(self, content: str) -> Dict:
        """Parse OpenAI response into structured format"""
        try:
            # Try to parse as JSON first
            if content.strip().startswith('{'):
                return json.loads(content)
            
            # If not JSON, create structured response from text
            return {
                "analysis": {
                    "task_type": "general",
                    "main_language": "mixed",
                    "complexity": "medium",
                    "files_analyzed": 0,
                    "estimated_time": "5-10 minutes"
                },
                "summary": content[:500] + "..." if len(content) > 500 else content,
                "recommendations": self._extract_recommendations(content),
                "code_changes": [],
                "security_issues": [],
                "performance_issues": [],
                "next_steps": ["Review the analysis", "Implement suggested changes"]
            }
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON")
            return self._create_fallback_response(content)
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from text content"""
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if (line.startswith('- ') or line.startswith('* ') or 
                line.startswith('1. ') or line.startswith('2. ') or
                'recommend' in line.lower() or 'suggest' in line.lower()):
                recommendations.append(line.lstrip('- *123456789. '))
        
        return recommendations[:10]  # Limit to 10 recommendations
    
    def _create_fallback_response(self, content: str) -> Dict:
        """Create fallback response structure"""
        return {
            "analysis": {
                "task_type": "general",
                "main_language": "unknown",
                "complexity": "medium",
                "files_analyzed": 0,
                "estimated_time": "unknown"
            },
            "summary": "Analysis completed with basic parsing",
            "recommendations": [
                "Review the provided analysis",
                "Consider implementing suggested improvements",
                "Test changes thoroughly"
            ],
            "code_changes": [],
            "security_issues": [],
            "performance_issues": [],
            "next_steps": ["Review analysis", "Plan implementation"]
        }
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create error response"""
        return {
            "analysis": {
                "task_type": "error",
                "main_language": "unknown",
                "complexity": "unknown",
                "files_analyzed": 0,
                "estimated_time": "unknown"
            },
            "summary": f"Analysis failed: {error_message}",
            "recommendations": [
                "Check your OpenAI API configuration",
                "Verify your API key is valid",
                "Try again with a simpler request"
            ],
            "code_changes": [],
            "security_issues": [],
            "performance_issues": [],
            "next_steps": ["Fix configuration", "Retry analysis"],
            "error": error_message
        }
    
    def _simulate_analysis(self, task_description: str, project_structure: Dict) -> Dict:
        """Simulate analysis when OpenAI is not available"""
        logger.info("Using simulation mode for code analysis")
        
        # Analyze task type
        task_lower = task_description.lower()
        if any(word in task_lower for word in ['bug', 'fix', 'error', 'issue']):
            task_type = "bug_fix"
        elif any(word in task_lower for word in ['optimize', 'performance', 'speed', 'slow']):
            task_type = "optimization"
        elif any(word in task_lower for word in ['security', 'secure', 'vulnerability']):
            task_type = "security_review"
        elif any(word in task_lower for word in ['feature', 'add', 'implement', 'new']):
            task_type = "feature_development"
        else:
            task_type = "general_review"
        
        # Determine main language
        file_types = project_structure.get('file_types', {})
        main_language = "mixed"
        if '.py' in file_types:
            main_language = "Python"
        elif '.js' in file_types or '.ts' in file_types:
            main_language = "JavaScript/TypeScript"
        elif '.java' in file_types:
            main_language = "Java"
        elif '.cpp' in file_types or '.c' in file_types:
            main_language = "C/C++"
        
        # Generate recommendations based on task type
        recommendations = self._generate_task_recommendations(task_type, main_language)
        
        return {
            "analysis": {
                "task_type": task_type,
                "main_language": main_language,
                "complexity": "medium",
                "files_analyzed": project_structure.get('total_files', 0),
                "estimated_time": "10-20 minutes"
            },
            "summary": f"Simulated analysis for {task_type} task in {main_language} project",
            "recommendations": recommendations,
            "code_changes": self._generate_sample_code_changes(main_language, task_type),
            "security_issues": self._generate_security_suggestions(task_type),
            "performance_issues": self._generate_performance_suggestions(task_type),
            "next_steps": [
                "Review the simulated recommendations",
                "Configure OpenAI API for real analysis",
                "Implement suggested improvements"
            ]
        }
    
    def _generate_task_recommendations(self, task_type: str, language: str) -> List[str]:
        """Generate task-specific recommendations"""
        base_recommendations = [
            "Add comprehensive error handling",
            "Implement proper logging",
            "Add unit tests for critical functions",
            "Document complex logic with comments"
        ]
        
        if task_type == "bug_fix":
            base_recommendations.extend([
                "Review error logs and stack traces",
                "Add debugging statements",
                "Test edge cases thoroughly",
                "Consider input validation"
            ])
        elif task_type == "optimization":
            base_recommendations.extend([
                "Profile code to identify bottlenecks",
                "Optimize database queries",
                "Implement caching strategies",
                "Consider algorithmic improvements"
            ])
        elif task_type == "security_review":
            base_recommendations.extend([
                "Validate all user inputs",
                "Implement proper authentication",
                "Use parameterized queries",
                "Keep dependencies updated"
            ])
        elif task_type == "feature_development":
            base_recommendations.extend([
                "Plan the feature architecture",
                "Design clean APIs",
                "Consider backward compatibility",
                "Plan for scalability"
            ])
        
        return base_recommendations[:8]  # Limit to 8 recommendations
    
    def _generate_sample_code_changes(self, language: str, task_type: str) -> List[Dict]:
        """Generate sample code changes"""
        if language == "Python":
            return [{
                "file": "main.py",
                "type": "modification",
                "description": "Add error handling and logging",
                "code": """import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def improved_function():
    try:
        # Your existing code here
        result = process_data()
        logger.info("Processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in processing: {str(e)}")
        raise""",
                "line_numbers": "1-15"
            }]
        elif language == "JavaScript/TypeScript":
            return [{
                "file": "app.js",
                "type": "modification",
                "description": "Add async/await error handling",
                "code": """async function improvedFunction() {
    try {
        const result = await processData();
        console.log('Processing completed successfully');
        return result;
    } catch (error) {
        console.error('Error in processing:', error);
        throw error;
    }
}""",
                "line_numbers": "1-10"
            }]
        else:
            return []
    
    def _generate_security_suggestions(self, task_type: str) -> List[str]:
        """Generate security suggestions"""
        if task_type == "security_review":
            return [
                "Implement input validation and sanitization",
                "Use HTTPS for all communications",
                "Store passwords using secure hashing",
                "Implement rate limiting",
                "Keep all dependencies updated"
            ]
        return []
    
    def _generate_performance_suggestions(self, task_type: str) -> List[str]:
        """Generate performance suggestions"""
        if task_type == "optimization":
            return [
                "Optimize database queries with indexes",
                "Implement caching for frequently accessed data",
                "Use connection pooling",
                "Minimize memory allocations in loops",
                "Consider asynchronous processing"
            ]
        return []
    
    async def _simulate_streaming(self, task_description: str, project_structure: Dict) -> AsyncGenerator[str, None]:
        """Simulate streaming response"""
        response_parts = [
            "Analyzing project structure...\n",
            "Identifying main programming language...\n",
            "Reviewing code patterns...\n",
            "Checking for common issues...\n",
            "Generating recommendations...\n",
            "Preparing code examples...\n",
            "Finalizing analysis...\n"
        ]
        
        for part in response_parts:
            yield part
            await asyncio.sleep(0.5)  # Simulate processing time

