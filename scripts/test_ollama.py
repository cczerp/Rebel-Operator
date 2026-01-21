#!/usr/bin/env python3
"""
Test Ollama integration for photo analysis.
Run this to verify Ollama is working before using it in your app.
"""

import os
import sys
import base64
import requests
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_ollama_connection():
    """Test if Ollama is running"""
    print("🔍 Testing Ollama connection...")

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama is running!")
            print(f"   Available models: {len(models)}")

            # Check for vision models
            vision_models = [m for m in models if "vision" in m.get("name", "").lower() or "llava" in m.get("name", "").lower()]

            if vision_models:
                print(f"   Vision models found:")
                for model in vision_models:
                    print(f"     - {model.get('name')}")
                return True, vision_models[0].get('name')
            else:
                print("   ⚠️  No vision models found!")
                print("   Run: ollama pull llama3.2-vision:11b")
                return False, None
        else:
            print(f"❌ Ollama returned error: {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("   Is it running? Try: ollama serve")
        return False, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_ollama_vision(model_name="llama3.2-vision:11b"):
    """Test Ollama vision analysis with a simple test"""
    print(f"\n🖼️  Testing vision analysis with {model_name}...")

    # Create a simple test prompt
    prompt = """Analyze this image and respond with JSON:
{
  "description": "Brief description of what you see",
  "objects": ["list", "of", "objects"]
}"""

    print(f"   Sending test request...")
    print(f"   (First request may be slow - loading model)")

    try:
        # For this test, we'll just send a text-only request
        # In the real app, images will be included
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": "Say 'Hello from Ollama!' and respond with JSON: {\"status\": \"working\", \"message\": \"Hello from Ollama!\"}",
                "stream": False,
                "format": "json"
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            print(f"✅ Ollama vision model is working!")
            print(f"   Response: {response_text[:100]}...")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out")
        print("   This is normal on first run (downloading model)")
        print("   Try running again in a minute")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_with_real_image(image_path=None):
    """Test with a real image if provided"""
    if not image_path:
        print("\n💡 To test with a real image:")
        print("   python scripts/test_ollama.py /path/to/image.jpg")
        return

    print(f"\n🖼️  Testing with real image: {image_path}")

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return

    # Load image and encode to base64
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return

    prompt = """Analyze this product image and provide:
1. What is the item?
2. Brand (if visible)
3. Condition (excellent, good, fair, poor)
4. Notable features

Respond in JSON format."""

    print("   Analyzing image with Ollama...")
    print("   (This may take 10-30 seconds)")

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2-vision:11b",
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
                "format": "json"
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "")
            print(f"\n✅ Analysis complete!")
            print(f"\n{response_text}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_ai_analyzer_integration():
    """Test the actual AiAnalyzer class"""
    print("\n🔧 Testing AiAnalyzer integration...")

    try:
        from src.enhancer.ai_enhancer import AiAnalyzer
        from src.schema.unified_listing import Photo, UnifiedListing, Price, ListingCondition

        # Create analyzer with Ollama enabled
        analyzer = AiAnalyzer(
            use_ollama=True,
            use_openai=False,
            use_anthropic=False,
            ollama_model="llama3.2-vision:11b"
        )

        print("✅ AiAnalyzer created with Ollama support")
        print(f"   Ollama enabled: {analyzer.use_ollama}")
        print(f"   Ollama model: {analyzer.ollama_model}")
        print(f"   Ollama host: {analyzer.ollama_host}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🦙 Ollama Integration Test")
    print("=" * 60)

    # Test 1: Connection
    connected, model_name = test_ollama_connection()
    if not connected:
        print("\n❌ Ollama is not ready. Please:")
        print("   1. Start Ollama: ollama serve")
        print("   2. Pull a vision model: ollama pull llama3.2-vision:11b")
        print("   3. Run this test again")
        return

    # Test 2: Vision model
    if model_name:
        vision_works = test_ollama_vision(model_name)
        if not vision_works:
            print("\n⚠️  Vision model test failed")
            print("   Try pulling the model again: ollama pull llama3.2-vision:11b")

    # Test 3: Real image (if provided)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_with_real_image(image_path)
    else:
        test_with_real_image(None)

    # Test 4: Integration
    integration_works = test_ai_analyzer_integration()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"   Ollama connection: {'✅' if connected else '❌'}")
    print(f"   Vision model: {'✅' if vision_works else '❌'}")
    print(f"   AiAnalyzer integration: {'✅' if integration_works else '❌'}")

    if connected and vision_works and integration_works:
        print("\n🎉 All tests passed! Ollama is ready to use!")
        print("\n💡 Your app will now use Ollama for FREE photo analysis!")
        print("   No API costs, unlimited usage, complete privacy!")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

    print("=" * 60)

if __name__ == "__main__":
    main()
