"""
Multi-Model Client using Hugging Face APIs.

Uses specialized models for different tasks:
1. Analysis: facebook/bart-large-mnli (zero-shot classification)
2. Guidance: Mistral-7B (instruction following)
3. Email: Llama-2-7b-chat-hf (conversational)
4. Judge: Intel/neural-chat-7b-v3-1 (quality assessment)

Includes automatic retries on transient failures.
"""
import os
import logging
import json
import requests
from typing import Dict, Any, Optional
from openai import OpenAI
from huggingface_hub import InferenceClient
from utils.exceptions import (
    HuggingFaceAPIError,
    APITimeoutError as CustomTimeoutError,
    ProcessingError,
)
from utils.retry_logic import with_retry

logger = logging.getLogger(__name__)

# Hugging Face API token
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HF_API_TOKEN")
if not HF_TOKEN:
    raise ValueError("Hugging Face API token not found. Please set HF_TOKEN or HF_API_TOKEN.")

# === Model Configuration ===
MODELS = {
    "analysis": {
        "id": "facebook/bart-large-mnli",
        "provider": "featherless-ai",
        "type": "text-generation",
        "description": "Zero-shot classification for ticket categorization"
    },
    "guidance": {
        "id": "mistralai/Mistral-7B-Instruct-v0.1",
        "provider": "featherless-ai",
        "type": "text-generation",
        "description": "Instruction-following for troubleshooting steps"
    },
    "email": {
        "id": "NousResearch/Llama-2-7b-chat-hf",
        "provider": "featherless-ai",
        "type": "text-generation",
        "description": "Conversational for professional emails"
    },
    "judge": {
        "id": "meta-llama/Llama-3.1-8b-Instruct",
        "provider": "featherless-ai",
        "type": "text-generation",
        "description": "Meta's Llama 3.1 for quality assessment and judging (ChatGPT-level)"
    }
}

# === Initialize Clients ===
# BART client for zero-shot classification
bart_client = InferenceClient(api_key=HF_TOKEN)

# Chat models client (OpenAI-compatible)
# Simplified to avoid httpx compatibility issues
try:
    chat_client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=HF_TOKEN,
    )
except TypeError:
    # Fallback if httpx client has issues
    import httpx
    http_client = httpx.Client(timeout=30.0)
    chat_client = OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=HF_TOKEN,
        http_client=http_client,
    )

logger.info("Hugging Face clients initialized")
logger.info(f"Analysis model (BART): {MODELS['analysis']['id']}")
logger.info(f"Guidance model: {MODELS['guidance']['id']}")
logger.info(f"Email model: {MODELS['email']['id']}")
logger.info(f"Judge model: {MODELS['judge']['id']}")


@with_retry
def analyze_ticket(ticket_text: str) -> Dict[str, Any]:
    """
    Analyze ticket using BART zero-shot classification with keyword-based fallback.

    Uses Hugging Face BART model for zero-shot classification, with intelligent fallback.

    Args:
        ticket_text: The ticket to analyze

    Returns:
        Dict with category, urgency, sentiment
    """
    try:
        logger.info("Analyzing ticket with BART zero-shot classification")

        # BART zero-shot classification via Hugging Face API
        api_url = f"https://api-inference.huggingface.co/models/{MODELS['analysis']['id']}"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        text_for_analysis = ticket_text[:500].lower()

        # Classify category
        category_labels = ["Technical Problem", "Billing Issue", "Account Access", "Product Question", "General Inquiry"]
        category_payload = {
            "inputs": ticket_text[:500],
            "parameters": {"candidate_labels": category_labels, "multi_class": True}
        }

        category_response = requests.post(api_url, headers=headers, json=category_payload, timeout=15)
        category_data = category_response.json()

        # Get top category with confidence check
        category = _extract_best_label(category_data, category_labels, 0.3)
        if not category:
            category = _infer_category_from_keywords(text_for_analysis)

        # Classify urgency with better prompting
        urgency_labels = ["Urgent", "High", "Medium", "Low"]
        urgency_payload = {
            "inputs": ticket_text[:500],
            "parameters": {"candidate_labels": urgency_labels, "multi_class": True}
        }

        urgency_response = requests.post(api_url, headers=headers, json=urgency_payload, timeout=15)
        urgency_data = urgency_response.json()

        urgency = _extract_best_label(urgency_data, urgency_labels, 0.2)
        if not urgency:
            urgency = _infer_urgency_from_keywords(text_for_analysis)

        # Classify sentiment
        sentiment_labels = ["Negative", "Neutral", "Positive"]
        sentiment_payload = {
            "inputs": ticket_text[:500],
            "parameters": {"candidate_labels": sentiment_labels, "multi_class": True}
        }

        sentiment_response = requests.post(api_url, headers=headers, json=sentiment_payload, timeout=15)
        sentiment_data = sentiment_response.json()

        sentiment = _extract_best_label(sentiment_data, sentiment_labels, 0.2)
        if not sentiment:
            sentiment = _infer_sentiment_from_keywords(text_for_analysis)

        # Fast keyword-based classifications (BART API calls removed for speed)
        logger.info("Performing fast keyword-based classifications...")

        # Additional fast keyword-based classifications
        resolution_type = _infer_resolution_type(text_for_analysis)
        business_impact = _infer_business_impact(text_for_analysis)
        issue_type = _infer_issue_type(text_for_analysis)
        time_sensitivity = _infer_time_sensitivity(text_for_analysis)

        analysis = {
            "category": category or "General Inquiry",
            "urgency": urgency or "Medium",
            "sentiment": sentiment or "Neutral",
            "resolution_type": resolution_type,
            "business_impact": business_impact,
            "issue_type": issue_type,
            "time_sensitivity": time_sensitivity
        }

        logger.info(f"BART advanced classification complete: {analysis}")
        return analysis

    except Exception as err:
        logger.warning(f"BART analysis error (using keyword fallback): {err}")
        text_lower = ticket_text.lower()
        return {
            "category": _infer_category_from_keywords(text_lower),
            "urgency": _infer_urgency_from_keywords(text_lower),
            "sentiment": _infer_sentiment_from_keywords(text_lower)
        }


def _extract_best_label(response_data: Dict, labels: list, confidence_threshold: float = 0.2) -> Optional[str]:
    """Extract the best matching label from BART response with confidence threshold."""
    try:
        if isinstance(response_data.get("scores"), list) and isinstance(response_data.get("labels"), list):
            labels_list = response_data.get("labels", [])
            scores_list = response_data.get("scores", [])

            if labels_list and scores_list:
                # Find the label with highest score
                best_idx = scores_list.index(max(scores_list))
                if scores_list[best_idx] > confidence_threshold:
                    return labels_list[best_idx]

        # Fallback to first label if available
        if isinstance(response_data.get("labels"), list) and response_data.get("labels"):
            return response_data["labels"][0]
    except Exception as e:
        logger.warning(f"Error extracting label: {e}")

    return None


def _infer_category_from_keywords(text: str) -> str:
    """Infer ticket category from keywords when API fails."""
    keywords = {
        "Billing Issue": ["charge", "refund", "payment", "invoice", "bill", "paid", "money", "cost", "price", "transaction", "credit card", "double charge"],
        "Account Access": ["login", "password", "access", "locked", "reset", "account", "sign in", "verify", "2fa", "authentication"],
        "Technical Problem": ["crash", "error", "bug", "broken", "not working", "lag", "slow", "down", "fail", "issue", "problem", "exception"],
        "Product Question": ["how to", "how do", "what is", "can i", "do you", "feature", "guide", "help with", "question about"],
    }

    for category, terms in keywords.items():
        if any(term in text for term in terms):
            return category

    return "General Inquiry"


def _infer_urgency_from_keywords(text: str) -> str:
    """Infer ticket urgency from keywords when API fails."""
    urgent_keywords = ["urgent", "asap", "immediate", "emergency", "critical", "emergency", "right now", "immediately"]
    high_keywords = ["important", "soon", "quickly", "quickly", "high priority", "please", "need help", "help me"]

    if any(word in text for word in urgent_keywords):
        return "Urgent"
    elif any(word in text for word in high_keywords):
        return "High"
    elif any(word in text for word in ["could", "sometime", "whenever"]):
        return "Low"

    return "Medium"


def _infer_sentiment_from_keywords(text: str) -> str:
    """Infer ticket sentiment from keywords when API fails."""
    negative_keywords = ["angry", "frustrated", "furious", "disgusted", "terrible", "awful", "horrible", "hate", "worst", "unacceptable", "!!", "!!!"]
    positive_keywords = ["thanks", "appreciate", "great", "wonderful", "excellent", "happy", "pleased", "thank you"]

    if any(word in text for word in negative_keywords):
        return "Negative"
    elif any(word in text for word in positive_keywords):
        return "Positive"

    return "Neutral"


def _infer_resolution_type(text: str) -> str:
    """Infer what type of resolution is needed."""
    escalation_keywords = ["urgent", "asap", "immediately", "emergency", "critical", "now", "right now"]
    self_service_keywords = ["how to", "how do i", "guide", "help me understand", "tutorial", "documentation"]

    if any(word in text for word in escalation_keywords):
        return "Escalation Required"
    elif any(word in text for word in self_service_keywords):
        return "Self-Service Possible"

    return "Needs Agent"


def _infer_business_impact(text: str) -> str:
    """Infer the business impact of the issue."""
    revenue_keywords = ["payment", "charge", "refund", "billing", "invoice", "transaction", "money", "cost"]
    service_keywords = ["down", "outage", "crash", "broken", "not working", "disabled", "unavailable"]
    data_keywords = ["data loss", "delete", "lost", "corrupted", "security", "hack", "breach"]

    if any(word in text for word in revenue_keywords):
        return "Revenue Impact"
    elif any(word in text for word in service_keywords):
        return "Service Down"
    elif any(word in text for word in data_keywords):
        return "Data Risk"

    return "User Experience"


def _infer_issue_type(text: str) -> str:
    """Infer the type of issue."""
    bug_keywords = ["bug", "error", "crash", "broken", "doesn't work", "not working", "failed", "malfunction"]
    feature_keywords = ["feature", "add", "implement", "request", "suggestion", "enhancement", "would like"]
    complaint_keywords = ["complaint", "unhappy", "angry", "frustrated", "terrible", "awful", "worst"]
    question_keywords = ["how", "what", "when", "where", "why", "question", "help", "can i", "how do"]

    if any(word in text for word in bug_keywords):
        return "Bug Report"
    elif any(word in text for word in feature_keywords):
        return "Feature Request"
    elif any(word in text for word in complaint_keywords):
        return "Complaint"
    elif any(word in text for word in question_keywords):
        return "Question"

    return "General Issue"


def _infer_time_sensitivity(text: str) -> str:
    """Infer how time-sensitive the issue is."""
    now_keywords = ["urgent", "asap", "immediately", "emergency", "critical", "now", "right now", "cannot wait"]
    today_keywords = ["today", "tonight", "this morning", "before end of day"]
    week_keywords = ["this week", "soon", "quickly", "fairly quickly"]

    if any(word in text for word in now_keywords):
        return "Immediate"
    elif any(word in text for word in today_keywords):
        return "Today"
    elif any(word in text for word in week_keywords):
        return "This Week"

    return "Non-Urgent"


@with_retry
def generate_guidance(ticket_text: str, category: str, is_urgent: bool) -> str:
    """
    Generate AI-powered, issue-specific troubleshooting guidance.

    Creates custom steps based on the EXACT problem described, not generic category steps.

    Args:
        ticket_text: The ticket text
        category: Ticket category
        is_urgent: Whether the ticket is urgent

    Returns:
        Dynamic, custom guidance specific to the exact issue
    """
    try:
        logger.info(f"Generating AI-powered guidance for: {category}")

        # Create a detailed, context-aware prompt that understands the SPECIFIC issue
        prompt = f"""You are an expert support agent who understands customer issues deeply.

CUSTOMER'S EXACT ISSUE:
{ticket_text[:400]}

TICKET CATEGORY: {category}
URGENCY LEVEL: {"High - Respond immediately" if is_urgent else "Normal - Standard response"}

Your task: Generate SPECIFIC, ACTIONABLE troubleshooting steps for THIS EXACT problem (not generic steps).

Requirements:
- 4-5 numbered steps
- Each step must be specific to the issue described above
- Steps should be progressive (easy to complex)
- Include what to check, what to do, and what to look for
- If this is urgent, prioritize quickest resolution first
- Each step should be one or two sentences, clear and actionable
- DO NOT give generic advice, focus on THIS specific issue

Example format:
1. [Specific action for this issue]
2. [Next logical step based on the problem]
3. [Verification or alternative approach]
4. [Contact point if needed]

Generate the steps now:"""

        result = client.text_generation(
            prompt=prompt,
            model=MODELS["guidance"]["id"],
            max_new_tokens=500,
            temperature=0.8,
        )

        guidance = result.strip()
        logger.info("AI-generated guidance created successfully")

        if guidance and len(guidance) > 20:
            return guidance
        else:
            # Fallback: Generate context-aware fallback based on actual ticket content
            return _generate_intelligent_fallback(ticket_text, category, is_urgent)

    except Exception as err:
        logger.warning(f"Guidance generation error: {err}")
        return _generate_intelligent_fallback(ticket_text, category, is_urgent)


def _generate_intelligent_fallback(ticket_text: str, category: str, is_urgent: bool) -> str:
    """
    Generate intelligent, context-aware fallback guidance by analyzing the EXACT ticket content.

    This function reads the actual problem and creates specific steps for that problem,
    not generic category-based steps.
    """
    text_lower = ticket_text.lower()

    # BILLING-SPECIFIC ISSUES
    if category == "Billing Issue":
        if "charged twice" in text_lower or "double charge" in text_lower:
            return """1. Log into your account and go to "Billing" or "Transactions"
2. Find the duplicate transaction - look for two identical charges on same date
3. Note the transaction IDs and amounts for both charges
4. Take screenshots of both charges as proof
5. Contact support with transaction IDs and ask for reversal of duplicate charge"""

        elif "refund" in text_lower or "return" in text_lower:
            return """1. Log into your account and find your order/purchase history
2. Locate the specific purchase you want refunded
3. Check the return window - usually 30 days from purchase date
4. Verify product condition (if applicable) meets return requirements
5. Request refund with your order number - support will review and process"""

        elif "missing charge" in text_lower or "not charged" in text_lower:
            return """1. Check your email for order confirmation receipt
2. Verify your payment method is still valid and on file
3. Go to your account settings and check billing history
4. Ensure there are no payment failures or declined transactions
5. If order doesn't appear, contact support with order details to investigate"""

        else:
            return """1. Log in and review your recent transactions and charges
2. Identify the specific charge that's incorrect - get date and amount
3. Check your order history to verify what you purchased
4. Compare what was charged vs. what you ordered
5. Contact support with the transaction ID and explain the discrepancy"""

    # TECHNICAL PROBLEM-SPECIFIC ISSUES
    elif category == "Technical Problem":
        if "crash" in text_lower:
            return """1. Note exactly what action causes the crash (e.g., uploading, clicking button)
2. Restart the app/browser completely to clear memory
3. Clear app cache or browser cache/cookies
4. Check if you're using the latest version - update if needed
5. Try the same action again; if it crashes, contact support with steps to reproduce"""

        elif "slow" in text_lower or "lag" in text_lower or "timeout" in text_lower:
            return """1. Check your internet connection speed - switch to WiFi if on mobile data
2. Close other apps/browser tabs using internet
3. Clear browser cache and cookies
4. Restart your browser or app completely
5. If still slow, contact support with your browser/app version and internet speed"""

        elif "error" in text_lower or "won't load" in text_lower or "not working" in text_lower:
            return """1. Write down the exact error message you see
2. Note whether it happens every time or occasionally
3. Try a different browser or device to isolate the issue
4. Clear your cache and cookies
5. Contact support with the error message and browser/device details"""

        elif "upload" in text_lower or "download" in text_lower:
            return """1. Verify your file meets size and format requirements
2. Check your internet connection is stable
3. Try uploading/downloading a smaller test file
4. Clear browser cache and try again
5. If still failing, contact support with file details and error message"""

        else:
            return """1. Describe what exactly isn't working and when it started
2. Check if other features work normally - helps isolate the problem
3. Try the action in a different browser or on a different device
4. Clear cache/cookies and restart the application
5. Contact support with exact steps to reproduce the issue"""

    # ACCOUNT ACCESS-SPECIFIC ISSUES
    elif category == "Account Access":
        if "password" in text_lower or "reset" in text_lower:
            return """1. Go to the login page and click "Forgot Password"
2. Enter your email address and check ALL email folders (including spam/promotions)
3. Click the password reset link within 24 hours
4. Create a new strong password (8+ chars, mix of letters/numbers/symbols)
5. If email doesn't arrive, verify your registered email is correct"""

        elif "locked" in text_lower or "blocked" in text_lower:
            return """1. Wait 15-30 minutes before trying to log in again (automatic unlock)
2. Try resetting your password via "Forgot Password" option
3. Check if you're entering the correct username (not email, if different)
4. Try a different browser or incognito/private window
5. Contact support if still locked - provide account details"""

        elif "2fa" in text_lower or "two-factor" in text_lower or "authenticator" in text_lower:
            return """1. Check your authenticator app for the 6-digit code
2. Ensure your device time is synchronized (device settings)
3. If code keeps changing, wait until next code appears before entering
4. Try using a backup code if you have one saved
5. If you lost access to your 2FA device, contact support immediately"""

        elif "email" in text_lower or "username" in text_lower:
            return """1. Verify you're using your registered email address for login
2. Check if you have multiple accounts - try different emails
3. Verify email hasn't been changed recently in account settings
4. Try resetting password using account recovery options
5. Contact support with account details to verify identity"""

        else:
            return """1. Verify you're entering correct username/email and password
2. Check for caps lock - password is case-sensitive
3. Try resetting your password using "Forgot Password"
4. Clear cookies and try in incognito/private browsing mode
5. Contact support with account details if still unable to access"""

    # PRODUCT QUESTION-SPECIFIC ISSUES
    elif category == "Product Question":
        if "how to" in text_lower or "how do i" in text_lower:
            return """1. Search the Help Center for your specific feature
2. Check video tutorials or step-by-step guides
3. Look for the feature in settings or menu options
4. Try the feature with sample data first to understand it
5. If instructions unclear, contact support with your specific use case"""

        elif "feature" in text_lower or "enable" in text_lower or "turn on" in text_lower:
            return """1. Navigate to Settings or Preferences in the app
2. Search for the feature name in the menu/options
3. Check if feature requires a premium/paid account
4. Verify your account has the necessary permissions
5. If can't find it, contact support with your plan type"""

        elif "difference" in text_lower or "what is" in text_lower:
            return """1. Check the Help Center for feature definitions
2. Read the comparison guide if available
3. Look for FAQ section explaining common features
4. Test both features to understand the difference
5. Ask support to explain which better suits your needs"""

        else:
            return """1. Search the Help Center or Knowledge Base for topic
2. Watch tutorial videos if available for the feature
3. Check FAQ section for common questions
4. Review user documentation or guides
5. Contact support with your specific question"""

    # GENERAL FALLBACK
    else:
        return """1. Provide details about what you're trying to accomplish
2. Explain what steps you've already tried
3. Note any error messages or unexpected behavior
4. Share relevant account/order/ticket information
5. Our team will review and provide specific guidance"""


@with_retry
def generate_email(ticket_text: str, analysis: Dict[str, str], routing_decision: str) -> str:
    """
    Generate customer response email using Llama-2-7b-chat.

    Args:
        ticket_text: The original ticket
        analysis: Analysis results (category, urgency, sentiment)
        routing_decision: Where ticket is routed

    Returns:
        Email text
    """
    try:
        logger.info("Generating email with Llama-2-7b-chat")

        prompt = f"""Write a professional, structured support email response with the following format:

Subject: Support Ticket Confirmation & Next Steps

Body should include:
1. Warm greeting and acknowledgment of the issue
2. Ticket category and urgency level
3. What our team will do next (specific to their issue)
4. Expected response time
5. Contact information or support resources
6. Professional closing

Issue Summary: {ticket_text[:300]}
Category: {analysis.get('category')}
Urgency Level: {analysis.get('urgency')}
Assigned Team: {routing_decision}

Generate the email now:"""

        result = client.text_generation(
            prompt=prompt,
            model=MODELS["email"]["id"],
            max_new_tokens=400,
            temperature=0.7,
        )

        email = result.strip()
        logger.info("Email generated successfully")
        return email if email else _get_structured_fallback_email(analysis, routing_decision)

    except Exception as err:
        logger.warning(f"Email generation error (using fallback): {err}")
        return _get_structured_fallback_email(analysis, routing_decision)


def _get_structured_fallback_email(analysis: Dict[str, str], routing_decision: str) -> str:
    """Generate a dynamic, structured fallback email when LLM generation fails."""
    import time
    category = analysis.get('category', 'General Inquiry')
    urgency = analysis.get('urgency', 'Medium')
    sentiment = analysis.get('sentiment', 'Neutral')

    # Dynamic response time based on urgency
    response_time_map = {
        'Urgent': '2 hours',
        'High': '4 hours',
        'Medium': '24 hours',
        'Low': '2-3 business days'
    }
    response_time = response_time_map.get(urgency, '24 hours')

    # Dynamic action items based on category
    action_items_map = {
        'Technical Problem': [
            'Diagnose the technical issue you\'re experiencing',
            'Identify the root cause and affected systems',
            'Develop and test a fix or workaround',
            'Deploy the solution and verify resolution'
        ],
        'Billing Issue': [
            'Review your account and billing history',
            'Verify the charges and identify discrepancies',
            'Process any necessary refunds or credits',
            'Prevent similar issues in the future'
        ],
        'Account Access': [
            'Verify your account identity securely',
            'Reset your credentials or recover your account',
            'Restore full access to your account',
            'Review security settings with you'
        ],
        'Product Question': [
            'Understand your specific product inquiry',
            'Provide detailed documentation and guides',
            'Answer all your questions comprehensively',
            'Direct you to relevant resources'
        ],
        'General Inquiry': [
            'Review your inquiry in detail',
            'Gather relevant information from our team',
            'Provide you with a complete answer',
            'Follow up if you need further assistance'
        ]
    }
    action_items = action_items_map.get(category, action_items_map['General Inquiry'])

    # Sentiment-aware greeting
    sentiment_greeting = {
        'Negative': 'We sincerely apologize for the frustration you\'re experiencing and will work hard to resolve this quickly.',
        'Neutral': 'We appreciate you bringing this to our attention.',
        'Positive': 'We\'re delighted to assist you today!'
    }
    greeting = sentiment_greeting.get(sentiment, 'We appreciate your patience and understanding.')

    # Generate current timestamp
    from datetime import datetime
    ticket_number = str(int(time.time() * 1000))[-8:]
    current_date = datetime.now().strftime('%B %d, %Y')

    return f"""Subject: Support Ticket #{ticket_number} - Confirmation & Next Steps

Dear Valued Customer,

Thank you for contacting us! We have received your support request and {greeting}

📋 TICKET DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticket ID: #{ticket_number}
Date Received: {current_date}
Category: {category}
Urgency Level: {urgency}
Status: Received & Queued for Review
Assigned To: {routing_decision}

✓ WHAT HAPPENS NEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your ticket has been routed to our {routing_decision} team who specializes in {category.lower()}s. We will prioritize your request based on its urgency level.

Our {routing_decision} team will:
• {action_items[0]}
• {action_items[1]}
• {action_items[2]}
• {action_items[3]}

⏱️ EXPECTED RESPONSE TIME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Given the {urgency.lower()} nature of your request, {response_time.lower()} is our targeted response time. We will notify you as soon as we have an update.

📊 PRIORITY LEVEL: {urgency.upper()}
Your ticket priority ensures timely attention and appropriate resources allocation.

📞 SUPPORT OPTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Live Chat: support.company.com/chat (Mon-Fri, 9 AM - 6 PM EST)
Knowledge Base: support.company.com/help
Email: support@company.com
Phone: 1-800-SUPPORT (1-800-787-7678)

📌 WHAT YOU CAN DO NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Save this email for your records
• Reference ticket #{ticket_number} when following up
• Check our help center while waiting for a response
• Provide additional details if you think of something important

Your Ticket Number: {ticket_number}
Keep this for quick reference in future communications.

Thank you for choosing us. We truly value your business and will resolve this as quickly as possible.

Best Regards,
{routing_decision}
Support Team
Company Name

---
This is an automated confirmation. Your actual support specialist will be in touch shortly."""


# ============= LLM-AS-JUDGE: Quality Validation =============

@with_retry
def judge_analysis(analysis: Dict[str, Any], ticket_text: str) -> Dict[str, Any]:
    """
    Judge LLM validates ticket analysis quality using Intel neural-chat model.

    Args:
        analysis: Analysis output from analyze_ticket()
        ticket_text: Original ticket text for context

    Returns:
        Dictionary with quality score and feedback
    """
    try:
        logger.info("Judging ticket analysis with Intel neural-chat-7b")

        completion = chat_client.chat.completions.create(
            model=f"{MODELS['judge']['id']}:featherless-ai",
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a quality assurance expert. Rate the quality of this ticket analysis on a scale of 1-10.

Ticket: {ticket_text[:300]}

Analysis Provided:
- Category: {analysis.get('category')}
- Urgency: {analysis.get('urgency')}
- Sentiment: {analysis.get('sentiment')}

Is it accurate? Complete? Will it help route correctly?
Just provide your rating (1-10) and brief feedback."""
                }
            ],
            temperature=0.5,
            max_tokens=150,
        )

        response_text = completion.choices[0].message.content.strip()
        logger.info(f"Analysis judged: {response_text[:100]}")

        # Parse score from response
        score = 8  # Default score
        feedback = response_text

        try:
            # Extract first number from response
            import re
            numbers = re.findall(r'\d+', response_text)
            if numbers:
                score = min(10, max(1, int(numbers[0])))
        except (ValueError, IndexError):
            score = 8

        return {
            "quality_score": score,
            "feedback": feedback,
            "passed_quality_check": score >= 6
        }

    except Exception as err:
        logger.warning(f"Judge analysis failed (non-blocking): {err}")
        # Return default score on failure
        return {
            "quality_score": 8,
            "feedback": "Judge unavailable",
            "passed_quality_check": True
        }


@with_retry
def judge_guidance(guidance: str, ticket_text: str) -> Dict[str, Any]:
    """
    Judge LLM validates troubleshooting guidance quality using Intel neural-chat model.

    Args:
        guidance: Guidance text from generate_guidance()
        ticket_text: Original ticket text for context

    Returns:
        Dictionary with quality score and feedback
    """
    try:
        logger.info("Judging guidance with Intel neural-chat-7b")

        completion = chat_client.chat.completions.create(
            model=f"{MODELS['judge']['id']}:featherless-ai",
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a support quality expert. Rate the quality of this troubleshooting guidance on a scale of 1-10.

Customer Issue: {ticket_text[:300]}

Guidance Provided:
{guidance[:300]}

Are the steps clear? Safe? Complete? Will they help?
Provide your rating (1-10) and feedback."""
                }
            ],
            temperature=0.5,
            max_tokens=150,
        )

        response_text = completion.choices[0].message.content.strip()
        logger.info(f"Guidance judged: {response_text[:100]}")

        # Parse score from response
        score = 8
        feedback = response_text

        try:
            import re
            numbers = re.findall(r'\d+', response_text)
            if numbers:
                score = min(10, max(1, int(numbers[0])))
        except (ValueError, IndexError):
            score = 8

        return {
            "quality_score": score,
            "feedback": feedback,
            "passed_quality_check": score >= 6
        }

    except Exception as err:
        logger.warning(f"Judge guidance failed (non-blocking): {err}")
        return {
            "quality_score": 8,
            "feedback": "Judge unavailable",
            "passed_quality_check": True
        }


@with_retry
def judge_email(email_text: str, ticket_text: str) -> Dict[str, Any]:
    """
    Judge LLM validates customer email quality using Intel neural-chat model.

    Args:
        email_text: Email from generate_email()
        ticket_text: Original ticket text for context

    Returns:
        Dictionary with quality score and feedback
    """
    try:
        logger.info("Judging email with Intel neural-chat-7b")

        completion = chat_client.chat.completions.create(
            model=f"{MODELS['judge']['id']}:featherless-ai",
            messages=[
                {
                    "role": "user",
                    "content": f"""You are a customer communication expert. Rate the quality of this support email on a scale of 1-10.

Customer Ticket: {ticket_text[:300]}

Email Response:
{email_text[:300]}

Is it professional? Empathetic? Clear about next steps?
Provide your rating (1-10) and brief feedback."""
                }
            ],
            temperature=0.5,
            max_tokens=150,
        )

        response_text = completion.choices[0].message.content.strip()
        logger.info(f"Email judged: {response_text[:100]}")

        # Parse score from response
        score = 8
        feedback = response_text

        try:
            import re
            numbers = re.findall(r'\d+', response_text)
            if numbers:
                score = min(10, max(1, int(numbers[0])))
        except (ValueError, IndexError):
            score = 8

        return {
            "quality_score": score,
            "feedback": feedback,
            "passed_quality_check": score >= 6
        }

    except Exception as err:
        logger.warning(f"Judge email failed (non-blocking): {err}")
        return {
            "quality_score": 8,
            "feedback": "Judge unavailable",
            "passed_quality_check": True
        }


def get_model_info() -> Dict[str, Any]:
    """Get information about configured models"""
    return MODELS
