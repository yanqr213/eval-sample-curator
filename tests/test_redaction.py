from eval_sample_curator.redaction import redact_text


def test_redacts_common_pii_patterns():
    text = (
        "Email alice@team.test, phone +1 (555) 123-4567, "
        "ssn 123-45-6789, card 4111 1111 1111 1111, ip 192.168.0.1"
    )

    redacted = redact_text(text)

    assert "alice@team.test" not in redacted
    assert "555" not in redacted
    assert "123-45-6789" not in redacted
    assert "4111" not in redacted
    assert "192.168.0.1" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
