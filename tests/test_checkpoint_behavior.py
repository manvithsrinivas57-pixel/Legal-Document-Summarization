"""Research integrity tests for BART checkpoint verification and missing checkpoint behavior."""

from pathlib import Path
import pytest
from agents.bart_summarizer import BARTSummarizerAgent
import config


def test_missing_checkpoint_strictly_halts_without_substituting_gemini(sample_judgment_text: str):
    """Test that when a fine-tuned checkpoint does not exist, the agent strictly stops

    with CHECKPOINT_MISSING status and does NOT substitute Gemini or fake output.
    """
    non_existent_path = Path("models/checkpoints/non_existent_run_model_12345")
    agent = BARTSummarizerAgent(checkpoint_path=non_existent_path, mode="fine_tuned")

    # Verify status
    status = agent.check_checkpoint_status()
    assert status["exists"] is False
    assert status["is_fine_tuned"] is False

    # Execute summarization
    result = agent.summarize(sample_judgment_text)

    # Strictly verify research integrity requirements
    assert result["status"] == "CHECKPOINT_MISSING"
    assert result["summary"] is None
    assert result["is_fine_tuned"] is False
    assert "RESEARCH INTEGRITY NOTICE" in result["explanation"]
    assert "silently substituted" in result["explanation"]
    assert "notebooks/civilsum_bart_finetuning.ipynb" in result["explanation"]


def test_config_is_checkpoint_available_validation(tmp_path: Path):
    """Test that is_checkpoint_available requires both config.json and model weights."""
    # Empty directory
    assert config.is_checkpoint_available(tmp_path) is False

    # Directory with only config.json
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    assert config.is_checkpoint_available(tmp_path) is False

    # Directory with config.json and model.safetensors
    (tmp_path / "model.safetensors").write_bytes(b"dummy_weights_header")
    assert config.is_checkpoint_available(tmp_path) is True


def test_tail_aware_trimming_preserves_lead_and_tail():
    """Test that Indian judgment tail-bias preprocessing preserves beginning and end."""
    agent = BARTSummarizerAgent()
    long_text = " ".join([f"word_{i}" for i in range(1500)])

    processed = agent._prepare_tail_aware_text(long_text, max_words=800)
    words = processed.split()

    # Must contain initial words (lead)
    assert "word_0" in processed
    assert "word_10" in processed
    # Must contain final words (tail holding)
    assert "word_1499" in processed
    assert "word_1490" in processed
    # Middle section omitted
    assert "[... procedural analysis omitted for token budget ...]" in processed
    assert len(words) < 1000


def test_distinguishes_pretrained_base_mode():
    """Test that mode='pretrained_base' is explicitly flagged as not fine-tuned."""
    agent = BARTSummarizerAgent(mode="pretrained_base")
    status = agent.check_checkpoint_status()
    assert status["mode"] == "pretrained_base"
    assert status["is_fine_tuned"] is False


def test_civilsum_trained_checkpoint_detected():
    """Verify that the fine-tuned CivilSum BART checkpoint is successfully detected."""
    checkpoint_dir = Path("models/checkpoints/civilsum_bart")
    assert checkpoint_dir.exists()
    weights_file = checkpoint_dir / "model.safetensors"
    if not weights_file.exists():
        pytest.skip("model.safetensors excluded in lightweight submission package (see README for setup instructions)")
    assert config.is_checkpoint_available(checkpoint_dir) is True
    agent = BARTSummarizerAgent(checkpoint_path=checkpoint_dir, mode="fine_tuned")
    status = agent.check_checkpoint_status()
    assert status["exists"] is True
    assert status["is_fine_tuned"] is True


def test_checkpoint_path_recorded_in_summarizer_status():
    """Regression test: checkpoint path and mode are explicitly captured in agent metadata."""
    agent = BARTSummarizerAgent(checkpoint_path="models/checkpoints/civilsum_bart", mode="fine_tuned")
    status = agent.check_checkpoint_status()
    assert "civilsum_bart" in status["checkpoint_path"]
    assert status["mode"] == "fine_tuned"

