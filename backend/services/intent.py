import json
from openai import OpenAI
from loguru import logger
from backend.config import settings

client = OpenAI(api_key=settings.openai_api_key)

# define all 5 intents as OpenAI functions
INTENT_FUNCTIONS = [
    {
        "name": "order_status",
        "description": "Customer wants to know the status of their order, where it is, or when it will arrive",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID mentioned by customer e.g. ORD12345"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer phone number if mentioned"
                }
            },
            "required": []
        }
    },
    {
    "name": "return_refund",
    "description": "Customer wants to return an item, request a refund, start a return process, check refund status, or report that they want to send a product back. Examples: 'I want to return my shoes', 'I need a refund', 'How do I return this item?', 'My product is damaged I want to send it back', 'Where is my refund?', 'I got the wrong item and want to return it'.",
    "parameters": {
        "type": "object",
        "properties": {
        "order_id": {
            "type": "string",
            "description": "Order ID mentioned by the customer if available"
        },
        "reason": {
            "type": "string",
            "description": "Reason for return such as damaged product, wrong item, size issue, not needed, or defective"
        }
        },
        "required": []
    }
    },
    {
        "name": "payment_issue",
        "description": "Customer has a payment problem — double charge, payment failed, not refunded",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID related to payment issue"
                },
                "issue_type": {
                    "type": "string",
                    "description": "Type of payment issue e.g. double charge, failed payment, missing refund"
                }
            },
            "required": []
        }
    },
    {
        "name": "delivery_complaint",
        "description": "Customer is complaining about delivery — late, wrong address, damaged in transit",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID for the delivery complaint"
                },
                "complaint_type": {
                    "type": "string",
                    "description": "Type of complaint e.g. late delivery, wrong address, damaged"
                }
            },
            "required": []
        }
    },
    {
        "name": "product_query",
        "description": "Customer is asking about a product — details, availability, size, colour, compatibility, or details of a product they bought like seller name",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Order ID if the customer mentions it"
                },
                "product_name": {
                    "type": "string",
                    "description": "Product name or type being asked about"
                },
                "query_type": {
                    "type": "string",
                    "description": "What they want to know e.g. availability, seller name, warranty, size, price, compatibility"
                }
            },
            "required": []
        }
    }
]


def classify_intent(text: str, conversation_history: list = []) -> dict:
    """
    Takes customer utterance + conversation history,
    returns detected intent + extracted entities.
    """
    try:
        # build messages — include history for multi-turn context
        messages = [
            {
                "role": "system",
                "content": """You are an intent classifier for ShopNow customer support.
                Classify the customer's intent into one of the provided functions.
                Extract any entities like order IDs, product names, or issue types.
                Consider the full conversation history for context.
                If the customer switches topic mid-conversation, detect the new intent.
                
                CRITICAL MULTI-LINGUAL RULE: Customers may speak in non-English languages (Hindi, Hinglish, etc.).
                You must intelligently translate their context and phonetics to map correctly to the required entities.
                For example, if a user verbally spells out an order number in Hindi or mixed languages (e.g., 'mera order O R D one two three' or uses Hindi script like 'ओआरडी'),
                explicitly normalize it back to 'ORD-123' format in pure English alphanumeric characters for the JSON output.
                NEVER output an order_id or customer_phone using Hindi numerals or Hindi script. Always convert to English letters and numbers (e.g. ORD-1001)."""
            },
            *conversation_history,
            {
                "role": "user",
                "content": text
            }
        ]

        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            functions=INTENT_FUNCTIONS,
            function_call="auto",
            max_tokens=200
        )

        message = response.choices[0].message

        # if a function was called — intent detected
        if message.function_call:
            intent_name = message.function_call.name
            entities    = json.loads(message.function_call.arguments)

            logger.info(f"Intent classified: {intent_name} | entities: {entities}")

            return {
                "intent":   intent_name,
                "entities": entities,
                "success":  True
            }

        # no function called — couldn't classify
        logger.warning(f"Could not classify intent for: {text}")
        return {
            "intent":   "unknown",
            "entities": {},
            "success":  False
        }

    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        return {
            "intent":   "unknown",
            "entities": {},
            "success":  False,
            "error":    str(e)
        }

if __name__ == "__main__":
    # test 1 — English
    result = classify_intent("Where is my order ORD12345?")
    print("Test 1:", result)

    # test 2 — Hinglish
    result = classify_intent("Mera payment do baar cut gaya")
    print("Test 2:", result)

    # test 3 — multi turn context
    history = [
        {"role": "user",      "content": "I want to return my shoes"},
        {"role": "assistant", "content": "Sure, what is your order ID?"},
    ]
    result = classify_intent("I want to return my shoes", history)
    print("Test 3:", result)