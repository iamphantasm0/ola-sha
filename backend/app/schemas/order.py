from app.models.order import Order


def serialize_order(order: Order | None) -> dict | None:
    if not order:
        return None
    return {
        "id": str(order.id),
        "status": order.status.value,
        "direction": order.direction,
        "token": order.token,
        "amount": float(order.amount) if order.amount is not None else None,
        "currency": order.currency,
        "rate": float(order.rate) if order.rate is not None else None,
        "output_amount": float(order.output_amount)
        if order.output_amount is not None
        else None,
        "paycrest_order_id": order.paycrest_order_id,
        "deposit_address": order.deposit_address,
        "valid_until": order.valid_until,
        "pay_bank_name": order.pay_bank_name,
        "pay_account_number": order.pay_account_number,
        "pay_account_name": order.pay_account_name,
        "pay_amount": order.pay_amount,
        "storage_hash": order.storage_hash,
        "registry_tx_hash": order.registry_tx_hash,
        "last_event": order.last_event,
        "last_event_message": order.last_event_message,
    }
