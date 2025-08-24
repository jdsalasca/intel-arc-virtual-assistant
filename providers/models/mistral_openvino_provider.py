"""
OpenVINO Model Provider for Intel-Optimized LLMs
Supports Mistral-7B with INT4 quantization and multi-device acceleration.
"""

import os
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Generator, Union
from pathlib import Path
import numpy as np

from core.interfaces.model_provider import (
    IModelProvider, ITextGenerator, IChatModel, DeviceType, ModelType
)
from core.models.conversation import Message, MessageRole

logger = logging.getLogger(__name__)

try:
    import openvino as ov
    from optimum.intel import OVModelForCausalLM
    from transformers import AutoTokenizer, TextIteratorStreamer
    import torch
    OPENVINO_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OpenVINO dependencies not available: {e}")
    OPENVINO_AVAILABLE = False
    ov = None
    OVModelForCausalLM = None
    AutoTokenizer = None
    TextIteratorStreamer = None
    torch = None

class MistralOpenVINOProvider(IModelProvider, ITextGenerator, IChatModel):
    """OpenVINO provider specifically optimized for Mistral-7B on Intel hardware."""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.model_path = None
        self.is_model_loaded = False
        self.core = None
        self.compiled_model = None
        
        # Intel-specific optimizations
        self.intel_config = {}
        
        # Performance tracking
        self.inference_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_inference_time": 0.0,
            "average_tokens_per_second": 0.0
        }
        
        # Mistral-specific configuration
        self.model_config = {
            "model_name": "mistralai/Mistral-7B-Instruct-v0.3",
            "supports_chat": True,
            "supports_streaming": True,
            "context_length": 8192,
            "quantization": "int4",
            "trust_remote_code": True
        }
    
    def load_model(self, model_path: str, device: DeviceType, **kwargs) -> bool:
        """Load Mistral-7B model with OpenVINO optimization."""
        if not OPENVINO_AVAILABLE:
            logger.error("OpenVINO dependencies not available")
            return False
        
        try:
            self.model_path = model_path
            self.device = device
            self.intel_config = kwargs
            
            logger.info(f"Loading Mistral-7B model from: {model_path}")
            logger.info(f"Target device: {device.value}")
            
            # Initialize OpenVINO core
            self.core = ov.Core()
            
            # Configure Intel optimizations
            self._configure_intel_optimizations(device, **kwargs)
            
            # Check if model is already converted to OpenVINO IR
            ir_model_path = Path(model_path)
            if ir_model_path.exists() and (ir_model_path / "openvino_model.xml").exists():
                logger.info("Loading pre-converted OpenVINO IR model")
                self._load_ir_model(ir_model_path, device)
            else:
                logger.info("Converting and loading model from HuggingFace")
                self._load_and_convert_model(model_path, device, **kwargs)
            
            # Load tokenizer
            self._load_tokenizer(model_path)
            
            # Validate model loading
            if self.model is not None and self.tokenizer is not None:
                self.is_model_loaded = True
                logger.info(f"✅ Mistral-7B loaded successfully on {device.value}")
                
                # Run a test inference to warm up
                self._warmup_model()
                return True
            else:
                logger.error("Failed to load model or tokenizer")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load Mistral-7B model: {e}")
            return False
    
    def _configure_intel_optimizations(self, device: DeviceType, **kwargs):
        """Configure Intel-specific optimizations."""
        # CPU optimizations
        if device in [DeviceType.CPU, DeviceType.AUTO]:
            self.core.set_property("CPU", {"PERFORMANCE_HINT": "THROUGHPUT"})
            self.core.set_property("CPU", {"CPU_THREADS_NUM": str(kwargs.get("num_threads", 0))})
            self.core.set_property("CPU", {"INFERENCE_PRECISION_HINT": "bf16"})
        
        # GPU optimizations  
        if device in [DeviceType.GPU, DeviceType.AUTO]:
            self.core.set_property("GPU", {"PERFORMANCE_HINT": "THROUGHPUT"})
            self.core.set_property("GPU", {"GPU_ENABLE_LOOP_UNROLLING": "YES"})
        
        # NPU optimizations
        if device in [DeviceType.NPU, DeviceType.AUTO]:
            self.core.set_property("NPU", {"PERFORMANCE_HINT": "LATENCY"})
    
    def _load_ir_model(self, model_path: Path, device: DeviceType):
        """Load pre-converted OpenVINO IR model."""
        try:
            # Load model with Optimum Intel
            self.model = OVModelForCausalLM.from_pretrained(
                model_path,
                device=device.value,
                ov_config={"PERFORMANCE_HINT": "THROUGHPUT"},
                compile=True
            )
            logger.info("OpenVINO IR model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load IR model: {e}")
            raise
    
    def _load_and_convert_model(self, model_path: str, device: DeviceType, **kwargs):
        """Load and convert HuggingFace model to OpenVINO IR."""
        try:
            # Convert model to OpenVINO with INT4 quantization
            logger.info("Converting model to OpenVINO IR with INT4 quantization...")
            
            # Use Optimum Intel for conversion and quantization
            self.model = OVModelForCausalLM.from_pretrained(
                model_path,
                export=True,
                device=device.value,
                ov_config={
                    "PERFORMANCE_HINT": "THROUGHPUT",
                    "INFERENCE_PRECISION_HINT": "bf16"
                },
                # Enable INT4 quantization
                load_in_4bit=True,
                compile=True
            )
            
            # Save converted model for future use
            converted_path = Path("models") / "mistral_7b_int4_ov"
            converted_path.mkdir(parents=True, exist_ok=True)
            self.model.save_pretrained(converted_path)
            logger.info(f"Converted model saved to: {converted_path}")
            
        except Exception as e:
            logger.error(f"Failed to convert model: {e}")
            raise
    
    def _load_tokenizer(self, model_path: str):
        """Load the tokenizer."""
        try:
            # Load tokenizer from original model
            if model_path.startswith("mistralai/"):
                tokenizer_path = model_path
            else:
                # For converted models, use original model name
                tokenizer_path = self.model_config["model_name"]
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_path,
                trust_remote_code=self.model_config["trust_remote_code"]
            )
            
            # Ensure pad token is set
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info("Tokenizer loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise
    
    def _warmup_model(self):
        """Warm up the model with a test inference."""
        try:
            test_input = "Hello, how are you?"
            _ = self.generate(test_input, max_tokens=10, temperature=0.7)
            logger.info("Model warmed up successfully")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    def unload_model(self) -> bool:
        """Unload the current model."""
        try:
            if self.model is not None:
                del self.model
                self.model = None
            
            if self.tokenizer is not None:
                del self.tokenizer
                self.tokenizer = None
            
            if self.compiled_model is not None:
                del self.compiled_model
                self.compiled_model = None
            
            self.is_model_loaded = False
            logger.info("Model unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload model: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.is_model_loaded and self.model is not None and self.tokenizer is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "name": "Mistral-7B-Instruct-v0.3",
            "provider": "OpenVINO",
            "device": self.device.value if self.device else None,
            "quantization": "INT4",
            "context_length": self.model_config["context_length"],
            "supports_chat": self.model_config["supports_chat"],
            "supports_streaming": self.model_config["supports_streaming"],
            "is_loaded": self.is_loaded(),
            "inference_stats": self.inference_stats.copy()
        }
    
    def get_supported_devices(self) -> List[DeviceType]:
        """Get list of supported devices."""
        if not OPENVINO_AVAILABLE:
            return []
        
        supported = [DeviceType.CPU]
        
        try:
            # Check available devices
            available_devices = self.core.available_devices if self.core else []
            
            if "GPU" in available_devices:
                supported.append(DeviceType.GPU)
            if "NPU" in available_devices:
                supported.append(DeviceType.NPU)
            
            supported.append(DeviceType.AUTO)
            
        except Exception as e:
            logger.warning(f"Failed to detect available devices: {e}")
        
        return supported
    
    def generate(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Generate text from a prompt."""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")
        
        start_time = time.time()
        
        try:
            # Prepare inputs
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=temperature > 0,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    **kwargs
                )
            
            # Decode response
            response_tokens = outputs[0][len(inputs.input_ids[0]):]
            response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
            # Apply stop sequences
            if stop_sequences:
                for stop_seq in stop_sequences:
                    if stop_seq in response:
                        response = response.split(stop_seq)[0]
            
            # Update stats
            inference_time = time.time() - start_time
            self._update_stats(len(response_tokens), inference_time)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def generate_stream(
        self, 
        prompt: str, 
        max_tokens: int = 256,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Generate text with streaming."""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")
        
        try:
            # Prepare inputs
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Create streamer
            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True
            )
            
            # Generation parameters
            generation_kwargs = {
                "input_ids": inputs.input_ids,
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "do_sample": temperature > 0,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "streamer": streamer,
                **kwargs
            }
            
            # Start generation in a separate thread
            import threading
            generation_thread = threading.Thread(
                target=self.model.generate,
                kwargs=generation_kwargs
            )
            generation_thread.start()
            
            # Stream tokens
            generated_text = ""
            for token in streamer:
                generated_text += token
                
                # Check stop sequences
                should_stop = False
                if stop_sequences:
                    for stop_seq in stop_sequences:
                        if stop_seq in generated_text:
                            # Return up to the stop sequence
                            final_text = generated_text.split(stop_seq)[0]
                            if final_text != generated_text:
                                yield final_text[len(generated_text) - len(token):]
                                should_stop = True
                                break
                
                if should_stop:
                    break
                
                yield token
            
            generation_thread.join()
            
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response for chat messages."""
        # Convert messages to Mistral chat format
        chat_prompt = self._format_chat_prompt(messages)
        return self.generate(
            chat_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop_sequences=["[/INST]", "</s>"],
            **kwargs
        )
    
    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """Generate chat response with streaming."""
        # Convert messages to Mistral chat format
        chat_prompt = self._format_chat_prompt(messages)
        yield from self.generate_stream(
            chat_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop_sequences=["[/INST]", "</s>"],
            **kwargs
        )
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Mistral chat template."""
        try:
            # Use tokenizer's chat template if available
            if hasattr(self.tokenizer, 'apply_chat_template'):
                return self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
        except Exception as e:
            logger.warning(f"Failed to use chat template: {e}")
        
        # Fallback to manual formatting
        formatted_messages = []
        
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            
            if role == "system":
                formatted_messages.append(f"<s>[INST] {content}")
            elif role == "user":
                if formatted_messages:
                    formatted_messages.append(f"[INST] {content} [/INST]")
                else:
                    formatted_messages.append(f"<s>[INST] {content} [/INST]")
            elif role == "assistant":
                formatted_messages.append(f"{content}</s>")
        
        # Add generation prompt if last message is user
        if messages and messages[-1].get("role") == "user":
            if not formatted_messages[-1].endswith("[/INST]"):
                formatted_messages[-1] += " [/INST]"
        
        return " ".join(formatted_messages)
    
    def _update_stats(self, tokens_generated: int, inference_time: float):
        """Update performance statistics."""
        self.inference_stats["total_requests"] += 1
        self.inference_stats["total_tokens"] += tokens_generated
        self.inference_stats["total_inference_time"] += inference_time
        
        if self.inference_stats["total_inference_time"] > 0:
            self.inference_stats["average_tokens_per_second"] = (
                self.inference_stats["total_tokens"] / 
                self.inference_stats["total_inference_time"]
            )