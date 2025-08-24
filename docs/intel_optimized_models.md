# Intel-Optimized Models for Virtual Assistant

## 🧠 Language Models (LLM) - OpenVINO Compatible

### Primary Options (Already in Use)
- **OpenVINO/Qwen2.5-7B-Instruct-int4-ov** ✅ (Current)
  - Size: ~4GB (INT4 quantized)
  - Performance: Excellent on Intel Arc GPU
  - Use case: Main reasoning and conversation

### Alternative/Backup Options
- **OpenVINO/Phi-3-mini-4k-instruct-int4-ov**
  - Size: ~2GB (INT4 quantized)
  - Performance: Faster, less capable
  - Use case: Quick responses, tool routing

- **OpenVINO/Llama-2-7b-chat-hf-int4-ov**
  - Size: ~4GB (INT4 quantized)
  - Performance: Good balance
  - Use case: Alternative main model

- **OpenVINO/TinyLlama-1.1B-Chat-v1.0-int4-ov**
  - Size: ~700MB (INT4 quantized)
  - Performance: Very fast, limited capability
  - Use case: NPU inference, lightweight tasks

## 🗣️ Text-to-Speech (TTS) - Intel NPU Optimized

### Recommended Options
- **microsoft/speecht5_tts** (with OpenVINO conversion)
  - Quality: High natural speech
  - NPU: Can be optimized for Intel AI Boost
  - Languages: English (primary)

- **espnet/kan-bayashi_ljspeech_vits** (convertible to OpenVINO)
  - Quality: Excellent voice synthesis
  - Performance: Good on Intel hardware
  - Real-time capable

### Alternative
- **suno/bark-small** (OpenVINO convertible)
  - Quality: Natural with emotions
  - Size: Larger model
  - Features: Can generate music/sounds

## 🎤 Speech-to-Text (STT) - Intel NPU Optimized

### Primary Choice
- **openai/whisper-base** (OpenVINO optimized)
  - Accuracy: Very good
  - Languages: Multilingual
  - NPU: Intel-optimized version available

- **openai/whisper-small** (OpenVINO optimized)
  - Accuracy: Better than base
  - Size: ~244MB
  - Real-time: Suitable for conversation

### Alternative
- **facebook/wav2vec2-base-960h** (OpenVINO convertible)
  - Accuracy: Good for English
  - Performance: Faster inference
  - Size: Smaller model

## 🖼️ Vision Models (Future Extension)

### For Multi-modal Capabilities
- **OpenVINO/blip-image-captioning-base**
  - Task: Image description
  - Performance: Intel-optimized

- **OpenVINO/clip-vit-base-patch32**
  - Task: Image-text understanding
  - Performance: Arc GPU accelerated

## 🚀 Performance Optimization Strategy

### Intel Arc GPU (Primary)
- Use **INT4 quantized models** for maximum throughput
- **Qwen2.5-7B** for main conversations
- **Phi-3-mini** for quick tool responses

### Intel AI Boost NPU (Secondary)
- **TinyLlama-1.1B** for simple tasks
- **Whisper-base** for speech recognition
- **TTS models** for voice synthesis

### CPU (Fallback)
- All models can fallback to CPU
- Optimized for Intel Core Ultra 7

## 📊 Model Selection Matrix

| Use Case | Model | Device | Size | Performance |
|----------|-------|--------|------|-------------|
| Main Chat | Qwen2.5-7B-int4 | Arc GPU | 4GB | High |
| Quick Tasks | Phi-3-mini-int4 | Arc GPU | 2GB | Fast |
| NPU Tasks | TinyLlama-1.1B | NPU | 700MB | Very Fast |
| Speech→Text | Whisper-base | NPU | 150MB | Real-time |
| Text→Speech | SpeechT5 | NPU | 500MB | Real-time |

## 🔧 Implementation Notes

### Model Loading Strategy
1. **Primary GPU**: Load Qwen2.5-7B for main conversations
2. **Secondary GPU**: Keep Phi-3-mini for tool routing
3. **NPU Pipeline**: Load TinyLlama + Whisper + TTS for voice

### Memory Management
- **GPU VRAM**: 8GB+ recommended for dual-model setup
- **System RAM**: 16GB+ for model caching
- **Storage**: SSD required for fast model switching

### Fallback Strategy
1. If Arc GPU unavailable → CPU inference
2. If NPU unavailable → CPU for voice tasks
3. Progressive model degradation based on system resources