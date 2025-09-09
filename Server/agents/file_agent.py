"""File Agent implementation for document and file processing."""

from typing import Dict, Any, List, Optional, AsyncIterator
from langgraph.graph import StateGraph, END
from .base import BaseAgent
from graphs.state import FileState
from tools.file_tools import DocumentProcessorTool, ImageAnalysisTool, CodeAnalysisTool


class FileAgent(BaseAgent):
    """Specialized agent for document and file processing."""
    
    def __init__(self):
        super().__init__("file_agent", "Document and file processing specialist")
        self.category = "file_processing"
        self.priority = 2
    
    def _initialize_tools(self) -> None:
        """Initialize tools available to this agent."""
        self.tools = {
            "document_processor": DocumentProcessorTool(),
            "image_analyzer": ImageAnalysisTool(),
            "code_analyzer": CodeAnalysisTool()
        }
    
    def _build_graph(self) -> None:
        """Build the agent's LangGraph workflow."""
        workflow = StateGraph(FileState)
        
        # Add nodes
        workflow.add_node("validate_files", self._validate_files)
        workflow.add_node("extract_content", self._extract_content)
        workflow.add_node("analyze_content", self._analyze_content)
        workflow.add_node("summarize_findings", self._summarize_findings)
        workflow.add_node("generate_insights", self._generate_insights)
        workflow.add_node("finalize_analysis", self._finalize_analysis)
        
        # Add edges
        workflow.set_entry_point("validate_files")
        workflow.add_edge("validate_files", "extract_content")
        workflow.add_edge("extract_content", "analyze_content")
        workflow.add_edge("analyze_content", "summarize_findings")
        workflow.add_edge("summarize_findings", "generate_insights")
        workflow.add_edge("generate_insights", "finalize_analysis")
        workflow.add_edge("finalize_analysis", END)
        
        self.graph = workflow.compile()
    
    async def process(self, state: FileState) -> FileState:
        """Process the current state and return updated state."""
        try:
            if not await self.validate_state(state):
                raise ValueError("Invalid state for FileAgent")
            
            # Run the graph
            result = await self.graph.ainvoke(state)
            return result
        
        except Exception as e:
            return await self.handle_error(e, state)
    
    async def stream(self, state: FileState) -> AsyncIterator[str]:
        """Stream processing results."""
        try:
            if not await self.validate_state(state):
                yield "Error: Invalid state for FileAgent"
                return
            
            # Run the graph with streaming
            async for chunk in self.graph.astream(state):
                if "finalize_analysis" in chunk:
                    response = chunk["finalize_analysis"].get("final_response", "")
                    if response:
                        yield response
                elif "analyze_content" in chunk:
                    analysis = chunk["analyze_content"].get("analysis_results", {})
                    if analysis:
                        yield f"Analyzing content: {analysis.get('summary', '')}"
        
        except Exception as e:
            yield f"Error in FileAgent: {str(e)}"
    
    async def _validate_files(self, state: FileState) -> FileState:
        """Validate uploaded files."""
        attachments = state.get("attachments", [])
        validated_files = []
        validation_errors = []
        
        for attachment in attachments:
            try:
                # Check file size
                file_size = len(attachment.get("data", ""))
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    validation_errors.append(f"File {attachment.get('filename', '')} is too large")
                    continue
                
                # Check file type
                mime_type = attachment.get("mime_type", "")
                if not self._is_supported_file_type(mime_type):
                    validation_errors.append(f"File {attachment.get('filename', '')} has unsupported type: {mime_type}")
                    continue
                
                # Check file content
                if not attachment.get("data"):
                    validation_errors.append(f"File {attachment.get('filename', '')} has no content")
                    continue
                
                validated_files.append(attachment)
            
            except Exception as e:
                validation_errors.append(f"Error validating {attachment.get('filename', '')}: {str(e)}")
        
        state["attachments"] = validated_files
        state["validation_errors"] = validation_errors
        state["processing_stage"] = "validated"
        
        return state
    
    async def _extract_content(self, state: FileState) -> Dict[str, Any]:
        """Extract content from validated files."""
        attachments = state.get("attachments", [])
        extraction_results = {}
        extraction_errors = []
        
        for attachment in attachments:
            try:
                filename = attachment.get("filename", "")
                mime_type = attachment.get("mime_type", "")
                file_data = attachment.get("data", "")
                
                # Determine processing tool based on file type
                if mime_type.startswith("image/"):
                    tool = self.tools["image_analyzer"]
                    result = await tool.execute(
                        image_data=file_data,
                        filename=filename,
                        mime_type=mime_type,
                        analysis_type="basic"
                    )
                elif self._is_code_file(filename, mime_type):
                    tool = self.tools["code_analyzer"]
                    result = await tool.execute(
                        file_data=file_data,
                        filename=filename,
                        mime_type=mime_type,
                        analysis_type="syntax"
                    )
                else:
                    tool = self.tools["document_processor"]
                    result = await tool.execute(
                        file_data=file_data,
                        filename=filename,
                        mime_type=mime_type,
                        processing_type="extract"
                    )
                
                extraction_results[filename] = result
                
            except Exception as e:
                extraction_errors.append(f"Error extracting {filename}: {str(e)}")
        
        state["extraction_results"] = extraction_results
        state["extraction_errors"] = extraction_errors
        state["processing_stage"] = "extracted"
        
        return state
    
    async def _analyze_content(self, state: FileState) -> Dict[str, Any]:
        """Analyze extracted content."""
        extraction_results = state.get("extraction_results", {})
        analysis_results = {}
        
        for filename, result in extraction_results.items():
            try:
                if result.get("status") == "success":
                    # Perform deeper analysis based on file type
                    analysis = await self._perform_deep_analysis(filename, result)
                    analysis_results[filename] = analysis
                else:
                    analysis_results[filename] = {
                        "status": "error",
                        "error": result.get("error", "Extraction failed")
                    }
            
            except Exception as e:
                analysis_results[filename] = {
                    "status": "error",
                    "error": str(e)
                }
        
        state["analysis_results"] = analysis_results
        state["processing_stage"] = "analyzed"
        
        return state
    
    async def _summarize_findings(self, state: FileState) -> Dict[str, Any]:
        """Summarize findings from analysis."""
        analysis_results = state.get("analysis_results", {})
        summary = {
            "total_files": len(analysis_results),
            "successful_analyses": 0,
            "failed_analyses": 0,
            "file_types": {},
            "key_findings": [],
            "recommendations": []
        }
        
        for filename, result in analysis_results.items():
            if result.get("status") == "success":
                summary["successful_analyses"] += 1
                
                # Categorize by file type
                file_type = self._get_file_type(filename)
                if file_type not in summary["file_types"]:
                    summary["file_types"][file_type] = 0
                summary["file_types"][file_type] += 1
                
                # Extract key findings
                findings = self._extract_key_findings(filename, result)
                summary["key_findings"].extend(findings)
                
            else:
                summary["failed_analyses"] += 1
        
        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations(summary)
        
        state["summary"] = summary
        state["processing_stage"] = "summarized"
        
        return state
    
    async def _generate_insights(self, state: FileState) -> Dict[str, Any]:
        """Generate insights from the analysis."""
        analysis_results = state.get("analysis_results", {})
        summary = state.get("summary", {})
        
        insights = {
            "overall_assessment": self._generate_overall_assessment(summary),
            "content_quality": self._assess_content_quality(analysis_results),
            "potential_issues": self._identify_potential_issues(analysis_results),
            "improvement_suggestions": self._generate_improvement_suggestions(analysis_results),
            "next_steps": self._suggest_next_steps(summary)
        }
        
        state["insights"] = insights
        state["processing_stage"] = "insights_generated"
        
        return state
    
    async def _finalize_analysis(self, state: FileState) -> Dict[str, Any]:
        """Finalize the analysis and create final response."""
        try:
            # Compile final response
            final_response = self._compile_final_response(state)
            
            state["final_response"] = final_response
            state["processing_stage"] = "completed"
            
        except Exception as e:
            state["tool_errors"]["finalization"] = str(e)
            state["final_response"] = "Error finalizing file analysis"
        
        return state
    
    def _is_supported_file_type(self, mime_type: str) -> bool:
        """Check if file type is supported."""
        supported_types = [
            # Images
            "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp", "image/bmp", "image/tiff",
            # Documents
            "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint", "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            # Text files
            "text/plain", "text/csv", "text/markdown", "text/xml",
            # Data files
            "application/json", "application/xml",
            # Code files
            "text/x-python", "application/javascript", "text/html", "text/css"
        ]
        return mime_type in supported_types
    
    def _is_code_file(self, filename: str, mime_type: str) -> bool:
        """Check if file is a code file."""
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs', '.html', '.css', '.sql', '.sh']
        return any(filename.lower().endswith(ext) for ext in code_extensions)
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type category."""
        if filename.lower().endswith(('.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs')):
            return "code"
        elif filename.lower().endswith(('.pdf', '.docx', '.doc')):
            return "document"
        elif filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            return "image"
        elif filename.lower().endswith(('.csv', '.xlsx', '.xls')):
            return "data"
        else:
            return "text"
    
    async def _perform_deep_analysis(self, filename: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep analysis on extracted content."""
        analysis = {
            "filename": filename,
            "status": "success",
            "content_length": result.get("content_length", 0),
            "extraction_method": result.get("extraction_method", "unknown"),
            "quality_score": self._calculate_quality_score(result),
            "complexity": self._assess_complexity(result),
            "key_topics": self._extract_key_topics(result),
            "metadata": result.get("analysis", {})
        }
        
        return analysis
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """Calculate quality score for extracted content."""
        content = result.get("content", "")
        if not content:
            return 0.0
        
        # Simple quality scoring based on content length and structure
        score = 0.5  # Base score
        
        # Length factor
        if len(content) > 1000:
            score += 0.2
        elif len(content) > 500:
            score += 0.1
        
        # Structure factor
        if "\n" in content:  # Has line breaks
            score += 0.1
        if "." in content:  # Has sentences
            score += 0.1
        if " " in content:  # Has spaces
            score += 0.1
        
        return min(score, 1.0)
    
    def _assess_complexity(self, result: Dict[str, Any]) -> str:
        """Assess complexity of extracted content."""
        content = result.get("content", "")
        if not content:
            return "unknown"
        
        word_count = len(content.split())
        
        if word_count < 100:
            return "simple"
        elif word_count < 500:
            return "medium"
        else:
            return "complex"
    
    def _extract_key_topics(self, result: Dict[str, Any]) -> List[str]:
        """Extract key topics from content."""
        content = result.get("content", "")
        if not content:
            return []
        
        # Simple keyword extraction
        words = content.lower().split()
        word_count = {}
        
        for word in words:
            if len(word) > 3 and word.isalpha():
                word_count[word] = word_count.get(word, 0) + 1
        
        # Get most common words
        common_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in common_words[:5] if count > 1]
    
    def _extract_key_findings(self, filename: str, result: Dict[str, Any]) -> List[str]:
        """Extract key findings from analysis result."""
        findings = []
        
        if result.get("status") == "success":
            content_length = result.get("content_length", 0)
            if content_length > 0:
                findings.append(f"{filename}: Successfully extracted {content_length} characters")
            
            analysis = result.get("analysis", {})
            if analysis:
                if analysis.get("has_tables"):
                    findings.append(f"{filename}: Contains tabular data")
                if analysis.get("has_code"):
                    findings.append(f"{filename}: Contains code elements")
                if analysis.get("word_count", 0) > 1000:
                    findings.append(f"{filename}: Large document with {analysis.get('word_count', 0)} words")
        
        return findings
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on summary."""
        recommendations = []
        
        if summary["failed_analyses"] > 0:
            recommendations.append("Review failed file analyses and ensure files are in supported formats")
        
        if summary["successful_analyses"] > 0:
            recommendations.append("Consider organizing files by type for better analysis")
        
        if "code" in summary["file_types"]:
            recommendations.append("Code files detected - consider running additional code analysis")
        
        if "image" in summary["file_types"]:
            recommendations.append("Image files detected - consider running image analysis for better insights")
        
        return recommendations
    
    def _generate_overall_assessment(self, summary: Dict[str, Any]) -> str:
        """Generate overall assessment of the files."""
        total_files = summary["total_files"]
        successful = summary["successful_analyses"]
        
        if total_files == 0:
            return "No files to analyze"
        elif successful == total_files:
            return "All files successfully analyzed"
        elif successful > total_files // 2:
            return "Most files successfully analyzed with some issues"
        else:
            return "Multiple file analysis issues detected"
    
    def _assess_content_quality(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall content quality."""
        quality_scores = []
        
        for filename, result in analysis_results.items():
            if result.get("status") == "success":
                quality_scores.append(result.get("quality_score", 0.5))
        
        if not quality_scores:
            return {"average_score": 0.0, "assessment": "No content to assess"}
        
        average_score = sum(quality_scores) / len(quality_scores)
        
        if average_score >= 0.8:
            assessment = "High quality content"
        elif average_score >= 0.6:
            assessment = "Good quality content"
        elif average_score >= 0.4:
            assessment = "Average quality content"
        else:
            assessment = "Low quality content"
        
        return {
            "average_score": average_score,
            "assessment": assessment,
            "total_files": len(quality_scores)
        }
    
    def _identify_potential_issues(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Identify potential issues in the analysis."""
        issues = []
        
        for filename, result in analysis_results.items():
            if result.get("status") == "error":
                issues.append(f"{filename}: {result.get('error', 'Unknown error')}")
            elif result.get("quality_score", 0) < 0.3:
                issues.append(f"{filename}: Low quality content extraction")
            elif result.get("complexity") == "complex" and result.get("content_length", 0) > 10000:
                issues.append(f"{filename}: Very large file may need specialized processing")
        
        return issues
    
    def _generate_improvement_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        
        for filename, result in analysis_results.items():
            if result.get("status") == "success":
                quality_score = result.get("quality_score", 0.5)
                if quality_score < 0.6:
                    suggestions.append(f"{filename}: Consider improving file format or content structure")
                
                complexity = result.get("complexity", "medium")
                if complexity == "complex":
                    suggestions.append(f"{filename}: Consider breaking down complex content into smaller sections")
        
        return suggestions
    
    def _suggest_next_steps(self, summary: Dict[str, Any]) -> List[str]:
        """Suggest next steps based on analysis."""
        next_steps = []
        
        if summary["successful_analyses"] > 0:
            next_steps.append("Review the extracted content and analysis results")
        
        if "code" in summary["file_types"]:
            next_steps.append("Consider running code quality analysis")
        
        if "image" in summary["file_types"]:
            next_steps.append("Consider running image analysis for better insights")
        
        if summary["failed_analyses"] > 0:
            next_steps.append("Address failed file analyses")
        
        return next_steps
    
    def _compile_final_response(self, state: FileState) -> str:
        """Compile the final response from all analysis results."""
        summary = state.get("summary", {})
        insights = state.get("insights", {})
        analysis_results = state.get("analysis_results", {})
        
        response_parts = []
        
        # Header
        response_parts.append("# File Analysis Report\n")
        
        # Summary
        response_parts.append("## Summary")
        response_parts.append(f"- **Total Files**: {summary.get('total_files', 0)}")
        response_parts.append(f"- **Successful Analyses**: {summary.get('successful_analyses', 0)}")
        response_parts.append(f"- **Failed Analyses**: {summary.get('failed_analyses', 0)}")
        response_parts.append("")
        
        # File Types
        if summary.get("file_types"):
            response_parts.append("## File Types")
            for file_type, count in summary["file_types"].items():
                response_parts.append(f"- **{file_type.title()}**: {count} files")
            response_parts.append("")
        
        # Key Findings
        if summary.get("key_findings"):
            response_parts.append("## Key Findings")
            for finding in summary["key_findings"]:
                response_parts.append(f"- {finding}")
            response_parts.append("")
        
        # Overall Assessment
        if insights.get("overall_assessment"):
            response_parts.append("## Overall Assessment")
            response_parts.append(insights["overall_assessment"])
            response_parts.append("")
        
        # Content Quality
        if insights.get("content_quality"):
            quality = insights["content_quality"]
            response_parts.append("## Content Quality")
            response_parts.append(f"- **Assessment**: {quality.get('assessment', 'Unknown')}")
            response_parts.append(f"- **Average Score**: {quality.get('average_score', 0):.2f}")
            response_parts.append("")
        
        # Potential Issues
        if insights.get("potential_issues"):
            response_parts.append("## Potential Issues")
            for issue in insights["potential_issues"]:
                response_parts.append(f"- {issue}")
            response_parts.append("")
        
        # Recommendations
        if summary.get("recommendations"):
            response_parts.append("## Recommendations")
            for recommendation in summary["recommendations"]:
                response_parts.append(f"- {recommendation}")
            response_parts.append("")
        
        # Next Steps
        if insights.get("next_steps"):
            response_parts.append("## Next Steps")
            for step in insights["next_steps"]:
                response_parts.append(f"- {step}")
            response_parts.append("")
        
        return "\n".join(response_parts)
