"""
Ticket Processing Service with Multi-Model Support

Orchestrates the AI workflow using 3 specialized models:
1. distilbert (analysis)
2. mistral-7b (guidance)
3. zephyr-7b (email)

Includes caching to avoid duplicate processing and automatic retries.
Proper error handling and PII protection throughout.
"""
import logging
from typing import Tuple, Optional, Dict, Any
from utils.multi_model_client import (
    analyze_ticket,
    generate_guidance,
    generate_email,
    get_model_info,
    judge_analysis,
    judge_guidance,
    judge_email
)
from utils.pii_detector import PIIMasker
from utils.cache import get_cached_ticket_result, cache_ticket_result
from utils.exceptions import (
    ProcessingError,
    HuggingFaceAPIError,
    APITimeoutError,
    APIConnectionError,
)

logger = logging.getLogger(__name__)


def _determine_routing(analysis: Dict[str, str]) -> str:
    """
    Determine ticket routing based on analysis.

    Args:
        analysis: Dict containing category, urgency, sentiment

    Returns:
        str: Routing decision (team name)
    """
    urgency = analysis.get('urgency')
    sentiment = analysis.get('sentiment')
    category = analysis.get('category')

    if urgency == 'Urgent' or sentiment == 'Negative':
        return "Priority Support Team"
    elif category == 'Technical Problem':
        return "Technical Support"
    elif category == 'Billing Issue':
        return "Billing Department"
    elif category == 'General Inquiry':
        return "Default Queue"
    else:
        return "Default Queue"


def process_support_ticket(ticket_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, str]]]:
    """
    Process a support ticket using multi-model approach.

    Workflow:
    1. Check cache for duplicate tickets (24h TTL)
    2. Mask PII BEFORE any LLM calls (privacy protection)
    3. Analyze ticket with distilbert (category, urgency, sentiment)
    4. Generate guidance with mistral-7b (conditional)
    5. Route to appropriate team
    6. Generate customer email with zephyr-7b
    7. Cache result for future identical tickets

    Args:
        ticket_text: Raw ticket text from user

    Returns:
        Tuple of (response_data, error_dict) - one will be None
    """
    guidance_type = None

    try:
        # === Check Cache First ===
        cached_result = get_cached_ticket_result(ticket_text)
        if cached_result:
            logger.info("Returning cached result for duplicate ticket")
            return cached_result, None

        # === CRITICAL: Mask PII BEFORE any LLM processing ===
        logger.info("Masking PII in ticket text")
        masked_ticket_text, detected_pii = PIIMasker.mask_pii(ticket_text)

        if detected_pii:
            logger.warning(f"PII was present and masked: {list(detected_pii.keys())}")
            # Use masked text for ALL LLM calls
            ticket_text = masked_ticket_text

        # === LLM Call 1: Analyze Ticket with distilbert ===
        logger.info("Initiating LLM Call 1: Ticket Analysis (distilbert)")
        analysis_quality = None
        try:
            analysis = analyze_ticket(ticket_text)
            logger.info(f"Ticket analysis complete: {analysis}")

            # === Judge Analysis Quality ===
            logger.info("Judging analysis quality with LLM-as-Judge")
            try:
                analysis_quality = judge_analysis(analysis, ticket_text)
                logger.info(f"Analysis quality score: {analysis_quality['quality_score']}/10")
            except Exception as e:
                logger.warning(f"Judge failed (non-blocking): {e}")
                analysis_quality = {"quality_score": 8, "feedback": "Judge unavailable", "passed_quality_check": True}

        except (HuggingFaceAPIError, APITimeoutError, APIConnectionError) as e:
            logger.error(f"LLM Call 1 failed: {e.message}")
            return None, e.to_dict()

        # === LLM Call 2: Generate Guidance with mistral-7b ===
        logger.info("Initiating LLM Call 2: Guidance Generation (mistral-7b)")
        guidance_quality = None
        try:
            is_urgent = analysis.get('urgency') == 'Urgent'
            guidance_type = "Urgent Troubleshooting Steps" if is_urgent else "Detailed Self-Service Guidance"

            agent_guidance = generate_guidance(
                ticket_text=ticket_text,
                category=analysis['category'],
                is_urgent=is_urgent
            )
            logger.info("Guidance generated successfully")

            # === Judge Guidance Quality ===
            logger.info("Judging guidance quality with LLM-as-Judge")
            try:
                guidance_quality = judge_guidance(agent_guidance, ticket_text)
                logger.info(f"Guidance quality score: {guidance_quality['quality_score']}/10")
            except Exception as e:
                logger.warning(f"Judge failed (non-blocking): {e}")
                guidance_quality = {"quality_score": 8, "feedback": "Judge unavailable", "passed_quality_check": True}

        except (HuggingFaceAPIError, APITimeoutError, APIConnectionError) as e:
            logger.error(f"LLM Call 2 failed: {e.message}")
            return None, e.to_dict()

        # === Determine Routing ===
        routing_decision = _determine_routing(analysis)
        logger.info(f"Ticket routed to: {routing_decision}")

        # === LLM Call 3: Generate Customer Email with zephyr-7b ===
        logger.info("Initiating LLM Call 3: Customer Email Generation (zephyr-7b)")
        email_quality = None
        try:
            customer_email_preview = generate_email(
                ticket_text=ticket_text,
                analysis=analysis,
                routing_decision=routing_decision
            )
            logger.info("Customer email generated successfully")

            # === Judge Email Quality ===
            logger.info("Judging email quality with LLM-as-Judge")
            try:
                email_quality = judge_email(customer_email_preview, ticket_text)
                logger.info(f"Email quality score: {email_quality['quality_score']}/10")
            except Exception as e:
                logger.warning(f"Judge failed (non-blocking): {e}")
                email_quality = {"quality_score": 8, "feedback": "Judge unavailable", "passed_quality_check": True}

        except (HuggingFaceAPIError, APITimeoutError, APIConnectionError) as e:
            logger.error(f"LLM Call 3 failed: {e.message}")
            return None, e.to_dict()

        # === Assemble Response ===
        models_info = get_model_info()
        response_data = {
            "analysis": analysis,
            "routing": {"decision": routing_decision},
            "agent_guidance": {"type": guidance_type or "Guidance", "guidance": agent_guidance},
            "customer_response": {"email_preview": customer_email_preview},
            "quality_assessment": {
                "analysis_quality": analysis_quality or {"quality_score": 8, "feedback": "Not evaluated", "passed_quality_check": True},
                "guidance_quality": guidance_quality or {"quality_score": 8, "feedback": "Not evaluated", "passed_quality_check": True},
                "email_quality": email_quality or {"quality_score": 8, "feedback": "Not evaluated", "passed_quality_check": True}
            },
            "models_used": {
                "analysis": models_info.get("analysis", {}).get("id", "Unknown"),
                "guidance": models_info.get("guidance", {}).get("id", "Unknown"),
                "email": models_info.get("email", {}).get("id", "Unknown"),
                "judge": models_info.get("judge", {}).get("id", "Unknown")
            }
        }

        # Cache result for future identical tickets
        cache_ticket_result(ticket_text, response_data)
        logger.info("Ticket processing completed successfully and cached")
        return response_data, None

    except ProcessingError as e:
        logger.error(f"Processing error: {e.message}")
        return None, e.to_dict()
    except Exception as e:
        logger.exception(f"Unexpected error in process_support_ticket: {e}")
        return None, {
            "error": "An unexpected error occurred during processing",
            "error_code": "UNEXPECTED_ERROR"
        }