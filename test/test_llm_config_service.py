from app.services import llm_config_service
from config.settings import BASE_DIR


def test_llm_config_deepseek_reasoning_switch_updates_model(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_config_service, "CONFIG_PATH", tmp_path / "llm.json")

    config = llm_config_service.save_llm_config(
        {
            "provider": "deepseek",
            "apiKey": "sk-test-deepseek",
            "reasoningEnabled": True,
        }
    )
    effective = llm_config_service.read_effective_llm_config()

    assert config["modelId"] == "deepseek-reasoner"
    assert effective["modelId"] == "deepseek-reasoner"
    assert effective["baseUrl"] == "https://api.deepseek.com/v1"


def test_llm_config_preset_uses_default_base_and_model(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_config_service, "CONFIG_PATH", tmp_path / "llm.json")

    config = llm_config_service.save_llm_config(
        {
            "provider": "openai",
            "apiKey": "sk-test-openai",
            "baseUrl": "ignored",
            "modelId": "ignored",
        }
    )
    effective = llm_config_service.read_effective_llm_config()

    assert config["baseUrl"] == "https://api.openai.com/v1"
    assert config["modelId"] == "gpt-5.2-chat-latest"
    assert config["apiKeyPreview"] == "sk-t********enai"
    assert effective["apiKey"] == "sk-test-openai"


def test_llm_config_custom_keeps_manual_base_and_model(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_config_service, "CONFIG_PATH", tmp_path / "llm.json")

    config = llm_config_service.save_llm_config(
        {
            "provider": "custom",
            "apiKey": "local-key",
            "baseUrl": "http://localhost:11434/v1",
            "modelId": "qwen-local",
        }
    )

    assert config["baseUrl"] == "http://localhost:11434/v1"
    assert config["modelId"] == "qwen-local"


def test_llm_config_blank_api_key_update_preserves_existing_key(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_config_service, "CONFIG_PATH", tmp_path / "llm.json")
    llm_config_service.save_llm_config({"provider": "openai", "apiKey": "sk-existing"})

    llm_config_service.save_llm_config({"provider": "siliconflow", "apiKey": None})
    effective = llm_config_service.read_effective_llm_config()

    assert effective["provider"] == "siliconflow"
    assert effective["apiKey"] == "sk-existing"


def test_llm_config_presets_include_glm_and_minimax():
    presets = llm_config_service.list_llm_presets()
    preset_ids = {item["id"] for item in presets}

    assert "glm" in preset_ids
    assert "minimax" in preset_ids


def test_llm_config_default_path_is_outside_repo():
    assert not llm_config_service.CONFIG_PATH.resolve().is_relative_to(BASE_DIR.resolve())
