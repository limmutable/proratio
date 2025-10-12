#!/usr/bin/env python3
"""
Check Available AI Models

Queries each AI provider to list available models with the configured API keys.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from proratio_utilities.config.settings import get_settings


def check_openai_models():
    """Check available OpenAI models"""
    print("=" * 70)
    print("  OpenAI (ChatGPT) Models")
    print("=" * 70)

    settings = get_settings()

    if not settings.openai_api_key or not settings.openai_api_key.startswith("sk-"):
        print("✗ No valid OpenAI API key configured")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        models = client.models.list()

        # Filter for GPT models only
        gpt_models = [m for m in models.data if "gpt" in m.id.lower()]
        gpt_models.sort(key=lambda x: x.id, reverse=True)

        print(f"\n✓ Found {len(gpt_models)} GPT models:\n")

        # Highlight latest/best models
        recommended = []
        for model in gpt_models[:15]:  # Show top 15
            marker = ""
            if "gpt-5" in model.id.lower():
                marker = " ⭐ (GPT-5 - LATEST)"
                recommended.append(model.id)
            elif "gpt-4o" in model.id.lower():
                marker = " 🔥 (GPT-4o - Advanced)"
                if not recommended:
                    recommended.append(model.id)
            elif "gpt-4-turbo" in model.id.lower():
                marker = " ✨ (GPT-4 Turbo)"

            print(f"  {model.id}{marker}")

        if recommended:
            print(f"\n💡 Recommended: {recommended[0]}")
            return recommended[0]
        elif gpt_models:
            print(f"\n💡 Recommended: {gpt_models[0].id}")
            return gpt_models[0].id

    except Exception as e:
        print(f"✗ Error checking OpenAI models: {e}")
        if "quota" in str(e).lower():
            print(
                "  ⚠️  API quota exceeded - add credits at https://platform.openai.com/billing"
            )
        return None

    return None


def check_anthropic_models():
    """Check available Anthropic models"""
    print("\n" + "=" * 70)
    print("  Anthropic (Claude) Models")
    print("=" * 70)

    settings = get_settings()

    if not settings.anthropic_api_key or not settings.anthropic_api_key.startswith(
        "sk-ant-"
    ):
        print("✗ No valid Anthropic API key configured")
        return None

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.anthropic_api_key)

        # Anthropic doesn't have a list models endpoint, so we try known models
        known_models = [
            "claude-opus-4-20250514",
            "claude-opus-4",
            "claude-sonnet-4-20250514",
            "claude-sonnet-4",
            "claude-3-7-sonnet-20250219",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

        print("\n✓ Testing known Claude models:\n")

        available = []
        for model in known_models:
            try:
                # Test with minimal request
                response = client.messages.create(
                    model=model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}],
                )
                marker = ""
                if "opus-4" in model:
                    marker = " ⭐ (Opus 4 - LATEST)"
                elif "sonnet-4" in model:
                    marker = " 🔥 (Sonnet 4.5 - Advanced)"
                elif "3-7" in model:
                    marker = " ✨ (Claude 3.7)"
                elif "3-5" in model:
                    marker = " ✨ (Claude 3.5)"

                print(f"  ✓ {model}{marker}")
                available.append(model)

                # Stop after finding first 3 working models
                if len(available) >= 3:
                    break

            except Exception as e:
                if "model" in str(e).lower():
                    continue  # Model not available
                else:
                    print(f"  ✗ {model} - {e}")

        if available:
            print(f"\n💡 Recommended: {available[0]}")
            return available[0]
        else:
            print("\n⚠️  No models responded successfully")
            print("   Defaulting to: claude-3-5-sonnet-20241022")
            return "claude-3-5-sonnet-20241022"

    except Exception as e:
        print(f"✗ Error checking Anthropic models: {e}")
        return None

    return None


def check_gemini_models():
    """Check available Google Gemini models"""
    print("\n" + "=" * 70)
    print("  Google (Gemini) Models")
    print("=" * 70)

    settings = get_settings()

    if not settings.gemini_api_key or len(settings.gemini_api_key) < 20:
        print("✗ No valid Google API key configured")
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)

        models = genai.list_models()

        # Filter for Gemini models that support generateContent
        gemini_models = [
            m
            for m in models
            if "gemini" in m.name.lower()
            and "generateContent" in m.supported_generation_methods
        ]

        print(f"\n✓ Found {len(gemini_models)} Gemini models:\n")

        recommended = []
        for model in gemini_models:
            model_id = model.name.replace("models/", "")
            marker = ""

            if "2.5-pro" in model_id.lower() or "2-5-pro" in model_id.lower():
                marker = " ⭐ (Gemini 2.5 Pro - LATEST)"
                recommended.append(model_id)
            elif "2.5-flash" in model_id.lower() or "2-5-flash" in model_id.lower():
                marker = " 🔥 (Gemini 2.5 Flash - Fast)"
                if not recommended:
                    recommended.append(model_id)
            elif "2.0" in model_id.lower():
                marker = " ✨ (Gemini 2.0)"
                if not recommended:
                    recommended.append(model_id)
            elif "1.5-pro" in model_id.lower():
                marker = " (Gemini 1.5 Pro)"
            elif "1.5-flash" in model_id.lower():
                marker = " (Gemini 1.5 Flash)"

            print(f"  {model_id}{marker}")

        if recommended:
            print(f"\n💡 Recommended: {recommended[0]}")
            return recommended[0]
        elif gemini_models:
            model_id = gemini_models[0].name.replace("models/", "")
            print(f"\n💡 Recommended: {model_id}")
            return model_id

    except Exception as e:
        print(f"✗ Error checking Gemini models: {e}")
        return None

    return None


if __name__ == "__main__":
    print("\n╔" + "═" * 68 + "╗")
    print("║" + " " * 22 + "AI Model Checker" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝\n")

    results = {}

    # Check each provider
    results["openai"] = check_openai_models()
    results["anthropic"] = check_anthropic_models()
    results["gemini"] = check_gemini_models()

    # Summary
    print("\n" + "=" * 70)
    print("  RECOMMENDED MODELS")
    print("=" * 70)
    print()

    if results["openai"]:
        print(f"OpenAI:    {results['openai']}")
    else:
        print("OpenAI:    ✗ Not available (quota/key issue)")

    if results["anthropic"]:
        print(f"Anthropic: {results['anthropic']}")
    else:
        print("Anthropic: ✗ Not available")

    if results["gemini"]:
        print(f"Gemini:    {results['gemini']}")
    else:
        print("Gemini:    ✗ Not available")

    print("\n" + "=" * 70)
    print()

    # Generate update commands
    if any(results.values()):
        print("📝 To update provider defaults, edit these files:\n")

        if results["openai"]:
            print("   proratio_signals/llm_providers/chatgpt.py")
            print(f"   → Change default model to: {results['openai']}\n")

        if results["anthropic"]:
            print("   proratio_signals/llm_providers/claude.py")
            print(f"   → Change default model to: {results['anthropic']}\n")

        if results["gemini"]:
            print("   proratio_signals/llm_providers/gemini.py")
            print(f"   → Change default model to: {results['gemini']}\n")
