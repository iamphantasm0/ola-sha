"""Tool definitions (OpenAI function-calling format) and the state->tools firewall.

Only the tools listed for the current state are injected into each Compute call,
and the dispatcher re-checks the same map before executing — double-gated.
"""

CURRENCIES = ["NGN", "KES", "UGX", "TZS", "MWK", "BRL"]
TOKENS = ["USDC", "USDT"]
NETWORKS = ["base", "polygon", "arbitrum", "ethereum", "bnb"]


ALL_TOOLS = {
    "get_offramp_quote": {
        "type": "function",
        "function": {
            "name": "get_offramp_quote",
            "description": (
                "Get the current exchange rate and payout for SELLING stablecoins for local "
                "currency. Call when the user wants to sell USDC/USDT and receive fiat."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "enum": TOKENS, "description": "Stablecoin to sell."},
                    "amount": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 4999,
                        "description": "Amount of stablecoin to sell (USD value).",
                    },
                    "currency": {
                        "type": "string",
                        "enum": CURRENCIES,
                        "description": "Local currency to receive. Default NGN.",
                    },
                },
                "required": ["token", "amount", "currency"],
            },
        },
    },
    "get_onramp_quote": {
        "type": "function",
        "function": {
            "name": "get_onramp_quote",
            "description": (
                "Get the current exchange rate and cost for BUYING stablecoins with local "
                "currency. Call when the user wants to buy USDC/USDT using a bank transfer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "enum": TOKENS, "description": "Stablecoin to buy."},
                    "amount": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 4999,
                        "description": "Amount of stablecoin to buy (USD value).",
                    },
                    "currency": {
                        "type": "string",
                        "enum": CURRENCIES,
                        "description": "Local currency to pay with.",
                    },
                },
                "required": ["token", "amount", "currency"],
            },
        },
    },
    "confirm_offramp": {
        "type": "function",
        "function": {
            "name": "confirm_offramp",
            "description": (
                "User has EXPLICITLY agreed to the offramp quote. Call ONLY after the user "
                "says yes/confirm/proceed. Never call speculatively."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    "confirm_onramp": {
        "type": "function",
        "function": {
            "name": "confirm_onramp",
            "description": (
                "User has EXPLICITLY agreed to the onramp quote. Call ONLY after the user "
                "says yes/confirm/proceed."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    "submit_bank_details": {
        "type": "function",
        "function": {
            "name": "submit_bank_details",
            "description": (
                "Submit the user's bank and account number for the fiat payout. The account "
                "holder NAME is fetched and verified automatically — do NOT ask the user for it. "
                "Call once you have the bank name and account number."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bank_name": {"type": "string", "description": "Bank name, e.g. GTBank, Access, UBA."},
                    "account_number": {
                        "type": "string",
                        "description": "Bank account number (10 digits for NGN).",
                    },
                },
                "required": ["bank_name", "account_number"],
            },
        },
    },
    "submit_wallet_address": {
        "type": "function",
        "function": {
            "name": "submit_wallet_address",
            "description": "Submit the user's wallet address for receiving stablecoins after onramp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "wallet_address": {
                        "type": "string",
                        "pattern": "^0x[a-fA-F0-9]{40}$",
                        "description": "EVM wallet address starting with 0x.",
                    },
                    "network": {
                        "type": "string",
                        "enum": NETWORKS,
                        "description": "Chain to receive the stablecoin on.",
                    },
                },
                "required": ["wallet_address", "network"],
            },
        },
    },
    "check_deposit_status": {
        "type": "function",
        "function": {
            "name": "check_deposit_status",
            "description": (
                "Check whether the user's stablecoin deposit has been detected by the provider. "
                "Call when the user asks for a status update after deposit instructions."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    "check_payment_status": {
        "type": "function",
        "function": {
            "name": "check_payment_status",
            "description": (
                "Check whether the user's bank transfer has been received by the provider. "
                "Call when the user claims they have sent payment."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    "cancel_order": {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": (
                "Cancel the current order. Call ONLY if the user explicitly asks to cancel. "
                "Do not cancel due to confusion or silence."
            ),
            "parameters": {
                "type": "object",
                "properties": {"reason": {"type": "string", "description": "Brief reason."}},
                "required": [],
            },
        },
    },
    "get_receipt": {
        "type": "function",
        "function": {
            "name": "get_receipt",
            "description": "Get the transaction receipt for the completed or failed order.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
}


TOOLS_BY_STATE = {
    "IDLE": ["get_offramp_quote", "get_onramp_quote"],
    # Offramp — submit_bank_details is allowed from QUOTING too: minimax tends to collapse the
    # confirm step, and if the submit tool isn't available it will hallucinate a deposit address.
    "OFFRAMP_QUOTING": [
        "confirm_offramp", "submit_bank_details", "get_offramp_quote", "get_onramp_quote", "cancel_order",
    ],
    "OFFRAMP_COLLECTING_BANK": ["submit_bank_details", "get_offramp_quote", "cancel_order"],
    "OFFRAMP_AWAITING_DEPOSIT": ["check_deposit_status", "cancel_order"],
    "OFFRAMP_PROCESSING": [],
    # Onramp
    "ONRAMP_QUOTING": [
        "confirm_onramp", "submit_wallet_address", "get_onramp_quote", "get_offramp_quote", "cancel_order",
    ],
    "ONRAMP_COLLECTING_WALLET": ["submit_wallet_address", "get_onramp_quote", "cancel_order"],
    "ONRAMP_AWAITING_PAYMENT": ["check_payment_status", "cancel_order"],
    "ONRAMP_PROCESSING": [],
    # Terminal
    "SETTLED": ["get_receipt", "get_offramp_quote", "get_onramp_quote"],
    "FAILED": ["get_receipt", "get_offramp_quote", "get_onramp_quote"],
    "CANCELLED": ["get_offramp_quote", "get_onramp_quote"],
}
