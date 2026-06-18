from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import CURRENCIES, NETWORKS
from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.models.user import SavedBankAccount, SavedWallet, User
from app.providers.paycrest import PaycrestProvider
from app.repositories.accounts import AccountRepository

router = APIRouter()
provider = PaycrestProvider()


def _bank_json(a: SavedBankAccount) -> dict:
    return {
        "id": str(a.id), "currency": a.currency, "bank_name": a.bank_name,
        "institution_code": a.institution_code, "account_number": a.account_number,
        "account_name": a.account_name, "label": a.label,
    }


def _wallet_json(w: SavedWallet) -> dict:
    return {"id": str(w.id), "address": w.address, "network": w.network, "label": w.label}


class AddBankRequest(BaseModel):
    currency: str
    bank_name: str
    account_number: str
    label: str | None = None


class AddWalletRequest(BaseModel):
    address: str
    network: str
    label: str | None = None


@router.get("/accounts")
async def list_accounts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    banks = await AccountRepository.list_banks(db, user.id)
    wallets = await AccountRepository.list_wallets(db, user.id)
    return {"bank_accounts": [_bank_json(b) for b in banks], "wallets": [_wallet_json(w) for w in wallets]}


@router.post("/accounts/bank")
async def add_bank(req: AddBankRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.currency not in CURRENCIES:
        raise HTTPException(status_code=400, detail="Unsupported currency")
    code = await provider.resolve_institution_code(req.currency, req.bank_name)
    if not code:
        raise HTTPException(status_code=400, detail=f"Could not match '{req.bank_name}' to a supported bank")
    try:
        name = await provider.verify_bank_account(code, req.account_number)
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Could not verify that account right now. Try again.")
    if not name:
        raise HTTPException(status_code=400, detail="Account could not be verified")
    acct = await AccountRepository.add_bank(
        db, user.id, req.currency, req.bank_name, code, req.account_number, name, req.label
    )
    return _bank_json(acct)


@router.delete("/accounts/bank/{account_id}")
async def delete_bank(account_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await AccountRepository.delete_bank(db, account_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


@router.post("/accounts/wallet")
async def add_wallet(req: AddWalletRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.network not in NETWORKS:
        raise HTTPException(status_code=400, detail="Unsupported network")
    if not (req.address.startswith("0x") and len(req.address) == 42):
        raise HTTPException(status_code=400, detail="Invalid EVM address")
    w = await AccountRepository.add_wallet(db, user.id, req.address, req.network, req.label)
    return _wallet_json(w)


@router.delete("/accounts/wallet/{wallet_id}")
async def delete_wallet(wallet_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await AccountRepository.delete_wallet(db, wallet_id, user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}
