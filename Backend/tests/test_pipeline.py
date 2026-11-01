from app.services.issue_detection import issue_detector
from app.services.priority import priority_calculator
from app.utils.file_handler import validate_audio_file, sanitize_filename

def test_sanitize_filename():
    assert sanitize_filename("../../some_path/call.wav") == "call.wav"
    assert sanitize_filename("call#$1.wav") == "call__1.wav"

def test_validate_audio_file():
    # Valid files
    assert validate_audio_file("call.wav", 1000) is True
    assert validate_audio_file("call.mp3", 5 * 1024 * 1024) is True
    # Invalid extensions
    assert validate_audio_file("call.txt", 1000) is False
    assert validate_audio_file("call.exe", 1000) is False
    # Exceeding size
    assert validate_audio_file("call.wav", 11 * 1024 * 1024) is False

def test_issue_detection():
    # Test billing terms
    assert issue_detector.detect_issue("My invoice is wrong and I was overcharged.") == "Billing"
    # Test refund terms
    assert issue_detector.detect_issue("I want a refund for the product.") == "Refund"
    # Test technical terms
    assert issue_detector.detect_issue("The application keeps throwing errors and is broken.") == "Technical Issue"
    # Test default
    assert issue_detector.detect_issue("Just a general question.") == "Other"

def test_priority_calculation():
    # Negative + high confidence -> HIGH
    p1 = priority_calculator.calculate_priority(
        sentiment="negative",
        confidence=0.92,
        issue="Subscription",
        transcript="Please cancel my subscription."
    )
    assert p1 == "HIGH"
    
    # Negative + medium confidence -> MEDIUM
    p2 = priority_calculator.calculate_priority(
        sentiment="negative",
        confidence=0.68,
        issue="Delivery",
        transcript="The delivery is late."
    )
    assert p2 == "MEDIUM"

    # Neutral -> NORMAL
    p3 = priority_calculator.calculate_priority(
        sentiment="neutral",
        confidence=0.8,
        issue="Account/Login",
        transcript="I want to update my username."
    )
    assert p3 == "NORMAL"

    # Legal/sue escalation keywords -> HIGH
    p4 = priority_calculator.calculate_priority(
        sentiment="negative",
        confidence=0.5,
        issue="Billing",
        transcript="I will sue your company unless you cancel my subscription."
    )
    assert p4 == "HIGH"
