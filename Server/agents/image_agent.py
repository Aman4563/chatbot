"""Image Agent implementation for image generation and processing."""

from typing import Dict, Any, List, Optional, AsyncIterator
from langgraph.graph import StateGraph, END
from .base import BaseAgent
from graphs.state import ImageState
from tools.image_tools import ImageGenerationTool, ImageProcessingTool, ImageAnalysisTool
from tools.llm_tools import LLMProviderTool, ResponseSynthesisTool


class ImageAgent(BaseAgent):
    """Specialized agent for image generation and processing."""
    
    def __init__(self):
        super().__init__("image_agent", "Image generation and processing specialist")
        self.category = "image_processing"
        self.priority = 4
    
    def _initialize_tools(self) -> None:
        """Initialize tools available to this agent."""
        self.tools = {
            "image_generator": ImageGenerationTool(),
            "image_processor": ImageProcessingTool(),
            "image_analyzer": ImageAnalysisTool(),
            "llm_provider": LLMProviderTool(),
            "response_synthesis": ResponseSynthesisTool()
        }
    
    def _build_graph(self) -> None:
        """Build the agent's LangGraph workflow."""
        workflow = StateGraph(ImageState)
        
        # Add nodes
        workflow.add_node("analyze_request", self._analyze_request)
        workflow.add_node("optimize_prompt", self._optimize_prompt)
        workflow.add_node("generate_image", self._generate_image)
        workflow.add_node("process_image", self._process_image)
        workflow.add_node("analyze_image", self._analyze_image)
        workflow.add_node("synthesize_response", self._synthesize_response)
        workflow.add_node("finalize_output", self._finalize_output)
        
        # Add edges
        workflow.set_entry_point("analyze_request")
        workflow.add_edge("analyze_request", "optimize_prompt")
        workflow.add_edge("optimize_prompt", "generate_image")
        
        # Conditional routing based on request type
        workflow.add_conditional_edges(
            "generate_image",
            self._should_process_image,
            {
                "process": "process_image",
                "analyze": "analyze_image"
            }
        )
        
        workflow.add_edge("process_image", "analyze_image")
        workflow.add_edge("analyze_image", "synthesize_response")
        workflow.add_edge("synthesize_response", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        self.graph = workflow.compile()
    
    async def process(self, state: ImageState) -> ImageState:
        """Process the current state and return updated state."""
        try:
            if not await self.validate_state(state):
                raise ValueError("Invalid state for ImageAgent")
            
            # Run the graph
            result = await self.graph.ainvoke(state)
            return result
        
        except Exception as e:
            return await self.handle_error(e, state)
    
    async def stream(self, state: ImageState) -> AsyncIterator[str]:
        """Stream processing results."""
        try:
            if not await self.validate_state(state):
                yield "Error: Invalid state for ImageAgent"
                return
            
            # Run the graph with streaming
            async for chunk in self.graph.astream(state):
                if "finalize_output" in chunk:
                    response = chunk["finalize_output"].get("final_response", "")
                    if response:
                        yield response
                elif "generate_image" in chunk:
                    generation_result = chunk["generate_image"].get("generation_result", {})
                    if generation_result:
                        yield f"Generating image: {generation_result.get('status', '')}"
                elif "optimize_prompt" in chunk:
                    optimized_prompt = chunk["optimize_prompt"].get("optimized_prompt", "")
                    if optimized_prompt:
                        yield f"Optimized prompt: {optimized_prompt[:100]}..."
        
        except Exception as e:
            yield f"Error in ImageAgent: {str(e)}"
    
    async def _analyze_request(self, state: ImageState) -> Dict[str, Any]:
        """Analyze the image generation request."""
        user_input = state.get("user_input", "")
        
        # Analyze request characteristics
        request_analysis = {
            "original_request": user_input,
            "request_type": self._classify_request_type(user_input),
            "image_style": self._detect_image_style(user_input),
            "image_subject": self._extract_image_subject(user_input),
            "image_quality": self._detect_quality_requirements(user_input),
            "image_size": self._detect_size_requirements(user_input),
            "image_count": self._detect_count_requirements(user_input),
            "processing_needed": self._detect_processing_requirements(user_input),
            "analysis_needed": self._detect_analysis_requirements(user_input)
        }
        
        state["request_analysis"] = request_analysis
        return state
    
    async def _optimize_prompt(self, state: ImageState) -> Dict[str, Any]:
        """Optimize the image generation prompt."""
        request_analysis = state.get("request_analysis", {})
        original_request = request_analysis.get("original_request", "")
        
        try:
            # Use LLM to optimize the prompt
            llm_tool = self.tools["llm_provider"]
            optimization_prompt = f"""Optimize this image generation prompt for better results:

Original prompt: "{original_request}"

Please provide an optimized prompt that:
1. Is clear and specific
2. Includes relevant artistic style keywords
3. Specifies important visual elements
4. Uses proper terminology for image generation
5. Is concise but descriptive

Optimized prompt:"""
            
            optimized_prompt = await llm_tool.execute(
                messages=[{"role": "user", "content": optimization_prompt}],
                provider="openai",
                model="gpt-4o",
                temperature=0.7,
                max_tokens=200
            )
            
            # Clean up the optimized prompt
            optimized_prompt = optimized_prompt.strip().strip('"').strip("'")
            
            state["optimized_prompt"] = optimized_prompt
            
        except Exception as e:
            # Fallback to original request if optimization fails
            state["optimized_prompt"] = original_request
            state["tool_errors"]["prompt_optimization"] = str(e)
        
        return state
    
    async def _generate_image(self, state: ImageState) -> Dict[str, Any]:
        """Generate image using the optimized prompt."""
        optimized_prompt = state.get("optimized_prompt", "")
        request_analysis = state.get("request_analysis", {})
        
        try:
            # Determine generation parameters
            image_size = request_analysis.get("image_size", "1024x1024")
            image_quality = request_analysis.get("image_quality", "standard")
            image_style = request_analysis.get("image_style", "vivid")
            
            # Generate image
            generator_tool = self.tools["image_generator"]
            generation_result = await generator_tool.execute(
                prompt=optimized_prompt,
                provider="openai",
                model="dall-e-3",
                size=image_size,
                quality=image_quality,
                style=image_style
            )
            
            if generation_result["status"] == "success":
                state["generated_images"] = [generation_result]
                state["generation_result"] = generation_result
            else:
                state["tool_errors"]["image_generation"] = generation_result.get("error", "Image generation failed")
        
        except Exception as e:
            state["tool_errors"]["image_generation"] = str(e)
        
        return state
    
    async def _process_image(self, state: ImageState) -> Dict[str, Any]:
        """Process generated image if needed."""
        generated_images = state.get("generated_images", [])
        request_analysis = state.get("request_analysis", {})
        
        if not generated_images:
            return state
        
        try:
            # Check if processing is needed
            if not request_analysis.get("processing_needed", False):
                return state
            
            # Process the first generated image
            image_result = generated_images[0]
            image_url = image_result.get("image_url", "")
            
            if image_url:
                # Download and process the image
                processed_result = await self._download_and_process_image(image_url, request_analysis)
                
                if processed_result:
                    state["processed_images"] = [processed_result]
                    state["processing_result"] = processed_result
        
        except Exception as e:
            state["tool_errors"]["image_processing"] = str(e)
        
        return state
    
    async def _analyze_image(self, state: ImageState) -> Dict[str, Any]:
        """Analyze generated or processed images."""
        generated_images = state.get("generated_images", [])
        processed_images = state.get("processed_images", [])
        request_analysis = state.get("request_analysis", {})
        
        try:
            # Analyze images if needed
            if not request_analysis.get("analysis_needed", False):
                return state
            
            images_to_analyze = processed_images if processed_images else generated_images
            
            if images_to_analyze:
                # Analyze the first image
                image_result = images_to_analyze[0]
                image_url = image_result.get("image_url", "")
                
                if image_url:
                    # Download and analyze the image
                    analysis_result = await self._download_and_analyze_image(image_url)
                    
                    if analysis_result:
                        state["image_analysis"] = analysis_result
        
        except Exception as e:
            state["tool_errors"]["image_analysis"] = str(e)
        
        return state
    
    async def _synthesize_response(self, state: ImageState) -> Dict[str, Any]:
        """Synthesize response from generation and analysis results."""
        try:
            # Collect all results
            generation_result = state.get("generation_result", {})
            processing_result = state.get("processing_result", {})
            image_analysis = state.get("image_analysis", {})
            request_analysis = state.get("request_analysis", {})
            
            # Prepare sources for synthesis
            sources = []
            
            # Add generation information
            if generation_result:
                sources.append({
                    "content": f"Generated image: {generation_result.get('prompt', '')}",
                    "source_type": "generation",
                    "metadata": generation_result
                })
            
            # Add processing information
            if processing_result:
                sources.append({
                    "content": f"Processed image with {processing_result.get('operation', '')}",
                    "source_type": "processing",
                    "metadata": processing_result
                })
            
            # Add analysis information
            if image_analysis:
                sources.append({
                    "content": f"Image analysis: {image_analysis.get('description', '')}",
                    "source_type": "analysis",
                    "metadata": image_analysis
                })
            
            # Synthesize response
            if sources:
                synthesis_tool = self.tools["response_synthesis"]
                synthesized_response = await synthesis_tool.execute(
                    sources=sources,
                    synthesis_type="combine"
                )
                state["synthesized_response"] = synthesized_response
            else:
                state["synthesized_response"] = "Image generation completed"
        
        except Exception as e:
            state["tool_errors"]["response_synthesis"] = str(e)
        
        return state
    
    async def _finalize_output(self, state: ImageState) -> Dict[str, Any]:
        """Finalize the output with proper formatting."""
        try:
            # Get all results
            generated_images = state.get("generated_images", [])
            processed_images = state.get("processed_images", [])
            image_analysis = state.get("image_analysis", {})
            synthesized_response = state.get("synthesized_response", "")
            request_analysis = state.get("request_analysis", {})
            
            # Compile final response
            final_response = self._compile_final_response(
                generated_images,
                processed_images,
                image_analysis,
                synthesized_response,
                request_analysis
            )
            
            state["final_response"] = final_response
            
        except Exception as e:
            state["tool_errors"]["output_finalization"] = str(e)
            state["final_response"] = "Error finalizing image output"
        
        return state
    
    def _classify_request_type(self, user_input: str) -> str:
        """Classify the type of image request."""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["generate", "create", "make", "draw"]):
            return "generation"
        elif any(word in user_input_lower for word in ["edit", "modify", "change", "adjust"]):
            return "editing"
        elif any(word in user_input_lower for word in ["analyze", "describe", "explain"]):
            return "analysis"
        elif any(word in user_input_lower for word in ["resize", "crop", "filter"]):
            return "processing"
        else:
            return "generation"
    
    def _detect_image_style(self, user_input: str) -> str:
        """Detect the desired image style."""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["realistic", "photorealistic", "photo"]):
            return "realistic"
        elif any(word in user_input_lower for word in ["cartoon", "anime", "manga"]):
            return "cartoon"
        elif any(word in user_input_lower for word in ["abstract", "artistic", "painting"]):
            return "abstract"
        elif any(word in user_input_lower for word in ["minimalist", "simple", "clean"]):
            return "minimalist"
        else:
            return "vivid"
    
    def _extract_image_subject(self, user_input: str) -> str:
        """Extract the main subject of the image."""
        # Simple subject extraction - in production, use more sophisticated NLP
        words = user_input.split()
        
        # Remove common words
        stop_words = {"generate", "create", "make", "draw", "image", "picture", "of", "a", "an", "the"}
        subject_words = [word for word in words if word.lower() not in stop_words]
        
        return " ".join(subject_words[:5])  # Take first 5 words as subject
    
    def _detect_quality_requirements(self, user_input: str) -> str:
        """Detect quality requirements from the request."""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["high quality", "hd", "4k", "ultra"]):
            return "hd"
        else:
            return "standard"
    
    def _detect_size_requirements(self, user_input: str) -> str:
        """Detect size requirements from the request."""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["large", "big", "wide", "landscape"]):
            return "1792x1024"
        elif any(word in user_input_lower for word in ["tall", "portrait", "vertical"]):
            return "1024x1792"
        elif any(word in user_input_lower for word in ["small", "tiny", "thumbnail"]):
            return "512x512"
        else:
            return "1024x1024"
    
    def _detect_count_requirements(self, user_input: str) -> int:
        """Detect how many images are requested."""
        user_input_lower = user_input.lower()
        
        if "multiple" in user_input_lower or "several" in user_input_lower:
            return 4
        elif "two" in user_input_lower or "pair" in user_input_lower:
            return 2
        elif "three" in user_input_lower or "triple" in user_input_lower:
            return 3
        else:
            return 1
    
    def _detect_processing_requirements(self, user_input: str) -> bool:
        """Detect if image processing is needed."""
        user_input_lower = user_input.lower()
        
        processing_keywords = ["resize", "crop", "filter", "blur", "sharpen", "grayscale", "edit", "modify"]
        return any(keyword in user_input_lower for keyword in processing_keywords)
    
    def _detect_analysis_requirements(self, user_input: str) -> bool:
        """Detect if image analysis is needed."""
        user_input_lower = user_input.lower()
        
        analysis_keywords = ["analyze", "describe", "explain", "what", "identify", "recognize"]
        return any(keyword in user_input_lower for keyword in analysis_keywords)
    
    async def _download_and_process_image(self, image_url: str, request_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Download and process an image."""
        try:
            import aiohttp
            import base64
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        image_base64 = base64.b64encode(image_data).decode()
                        
                        # Process image based on requirements
                        processor_tool = self.tools["image_processor"]
                        
                        # Determine processing operation
                        if "resize" in request_analysis.get("original_request", "").lower():
                            result = await processor_tool.execute(
                                image_data=image_base64,
                                operation="resize",
                                width=512,
                                height=512
                            )
                        elif "crop" in request_analysis.get("original_request", "").lower():
                            result = await processor_tool.execute(
                                image_data=image_base64,
                                operation="crop",
                                x=0,
                                y=0,
                                width=512,
                                height=512
                            )
                        else:
                            # Default processing
                            result = await processor_tool.execute(
                                image_data=image_base64,
                                operation="resize",
                                width=1024,
                                height=1024
                            )
                        
                        return result
            
        except Exception as e:
            print(f"Error downloading and processing image: {e}")
            return None
    
    async def _download_and_analyze_image(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Download and analyze an image."""
        try:
            import aiohttp
            import base64
            
            # Download image
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        image_base64 = base64.b64encode(image_data).decode()
                        
                        # Analyze image
                        analyzer_tool = self.tools["image_analyzer"]
                        result = await analyzer_tool.execute(
                            image_data=image_base64,
                            analysis_type="describe",
                            detail_level="high"
                        )
                        
                        return result
            
        except Exception as e:
            print(f"Error downloading and analyzing image: {e}")
            return None
    
    def _compile_final_response(self, generated_images: List[Dict[str, Any]], processed_images: List[Dict[str, Any]], image_analysis: Dict[str, Any], synthesized_response: str, request_analysis: Dict[str, Any]) -> str:
        """Compile the final response."""
        response_parts = []
        
        # Add main response
        if synthesized_response:
            response_parts.append(synthesized_response)
        else:
            response_parts.append("Image generation completed successfully!")
        
        # Add generated images
        if generated_images:
            response_parts.append("\n## Generated Images:")
            for i, image in enumerate(generated_images, 1):
                image_url = image.get("image_url", "")
                prompt = image.get("prompt", "")
                if image_url:
                    response_parts.append(f"\n### Image {i}")
                    response_parts.append(f"![Generated Image]({image_url})")
                    if prompt:
                        response_parts.append(f"*Prompt: {prompt}*")
        
        # Add processed images
        if processed_images:
            response_parts.append("\n## Processed Images:")
            for i, image in enumerate(processed_images, 1):
                processed_image = image.get("processed_image", "")
                operation = image.get("operation", "")
                if processed_image:
                    response_parts.append(f"\n### Processed Image {i}")
                    response_parts.append(f"![Processed Image](data:image/png;base64,{processed_image})")
                    if operation:
                        response_parts.append(f"*Operation: {operation}*")
        
        # Add image analysis
        if image_analysis:
            response_parts.append("\n## Image Analysis:")
            description = image_analysis.get("description", "")
            if description:
                response_parts.append(description)
            
            confidence = image_analysis.get("confidence", 0)
            if confidence:
                response_parts.append(f"*Confidence: {confidence:.2f}*")
        
        # Add generation details
        response_parts.append("\n## Generation Details:")
        response_parts.append(f"- **Request Type**: {request_analysis.get('request_type', 'generation')}")
        response_parts.append(f"- **Image Style**: {request_analysis.get('image_style', 'vivid')}")
        response_parts.append(f"- **Image Quality**: {request_analysis.get('image_quality', 'standard')}")
        response_parts.append(f"- **Image Size**: {request_analysis.get('image_size', '1024x1024')}")
        
        return "\n".join(response_parts)
    
    def _should_process_image(self, state: ImageState) -> str:
        """Determine if image should be processed."""
        request_analysis = state.get("request_analysis", {})
        generation_result = state.get("generation_result", {})
        
        if request_analysis.get("processing_needed", False) and generation_result.get("status") == "success":
            return "process"
        else:
            return "analyze"
