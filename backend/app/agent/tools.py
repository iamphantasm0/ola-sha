"""
Tool definitions in OpenAI function-calling format, plus the state gate.

Only the tools allowed for the current order state are injected into each
0G Compute Router call. The dispatcher re-checks the gate server-side, so a
hallucinated tool call can never execute out of state.
"""

ALL_TOOLS = {
    "get_offramp_quote": {
        "type": "function",
        "function": {
            "name": "get_offramp_quote",
            "description": (
                "Get the current exchange rate and calculate payout for selling "
                "stablecoins for local currency. Call this when the user wants to "
                "sell USDC or USDT and receive fiat money."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "enum": ["USDC", "USDT"],
                        "description": "The stablecoin to sell.",
                    },
                    "amount": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 4999,
                        "description": "Amount of stablecoin to sell (USD value).",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["NGN", "KES", "UGX", "TZS", "MWK", "BRL"],
                        "description": "Local currency to receive. Default NGN if unspecified.",
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
                "Get the current exchange rate and calculate cost for buying "
                "stablecoins with local currency. Call this when the user wants to "
                "buy USDC or USDT using cash or bank transfer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "enum": ["USDC", "USDT"],
                        "description": "The stablecoin to buy.",
                    },
                    "amount": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 4999,
                        "description": "Amount of stablecoin to buy (USD value).",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["NGN", "KES", "UGX", "TZS", "MWK", "BRL"],
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
                "User has explicitly agreed to the offramp rate quote. Call ONLY "
                "after the user says yes, confirms, or clearly accepts. Do not call "
                "speculatively."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    "confirm_onramp": {
        "type": "function",
        "function": {
            "name": "confirm_onramp",
            "description": (
                "User has explicitly agreed to the onramp rate quote. Call ONLY "
                "after the user says yes, confirms, or clearly accepts."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    "submit_bank_details": {
        "type": "function",
        "function": {
            "name": "submit_bank_details",
            "description": (
                "Submit the user's bank account details for receiving the fiat "
                "payout. Only call when you have ALL three fields from the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bank_name": {
                        "type": "string",
                        "description": "Bank name (e.g. GTBank, Access, UBA, Zenith).",
                    },
                    "account_number": {
                        "type": "string",
                        "pattern": "^[0-9]{10}$",
                        "description": "10-digit bank account number.",
                    },
                    "account_name": {
                        "type": "string",
                        "description": "Account holder name exactly as on the account.",
                    },
                },
                "required": ["bank_name", "account_number", "account_name"],
            },
        },
    },
    "submit_wallet_address": {
        "type": "function",
        "function": {
            "name": "submit_wallet_address",
            "description": (
                "Submit the user's wallet address for receiving stablecoins after "
                "onramp."
            ),
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
                        "enum": ["base", "polygon", "arbitrum", "ethereum", "bnb"],
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
                "Check whether the user's stablecoin deposit has been detected by "
                "Paycrest. Call when the user asks for a status update after being "
                "given deposit instructions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID from the current session.",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    "check_payment_status": {
        "type": "function",
        "function": {
            "name": "check_payment_status",
            "description": (
                "Check whether the user's fiat bank transfer has been received by "
                "Paycrest. Call when the user claims they have sent payment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID from the current session.",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    "cancel_order": {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": (
                "Cancel the current order. Call ONLY if the user explicitly asks to "
                "cancel. Do not cancel due to confusion or silence."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for cancellation.",
                    }
                },
                "required": [],
            },
        },
    },
    "get_receipt": {
        "type": "function",
        "function": {
            "name": "get_receipt",
            "description": "Get the transaction receipt for the completed or failed order.",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string"}},
                "required": ["order_id"],
            },
        },
    },
}


TOOLS_BY_STATE = {
    "IDLE": ["get_offramp_quote", "get_onramp_quote"],
    # Offramp
    "OFFRAMP_QUOTING": ["confirm_offramp", "cancel_order"],
    "OFFRAMP_COLLECTING_BANK": ["submit_bank_details", "cancel_order"],
    "OFFRAMP_AWAITING_DEPOSIT": ["check_deposit_status", "cancel_order"],
    "OFFRAMP_PROCESSING": [],  # backend is working; AI cannot act
    # Onramp
    "ONRAMP_QUOTING": ["confirm_onramp", "cancel_order"],
    "ONRAMP_COLLECTING_WALLET": ["submit_wallet_address", "cancel_order"],
    "ONRAMP_AWAITING_PAYMENT": ["check_payment_status", "cancel_order"],
    "ONRAMP_PROCESSING": [],  # backend is working; AI cannot act
    # Terminal
    "SETTLED": ["get_receipt", "get_offramp_quote", "get_onramp_quote"],
    "FAILED": ["get_receipt", "get_offramp_quote", "get_onramp_quote"],
    "CANCELLED": ["get_offramp_quote", "get_onramp_quote"],
}
