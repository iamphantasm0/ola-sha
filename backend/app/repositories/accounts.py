import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import SavedBankAccount, SavedWallet


class AccountRepository:
    # ─── Bank accounts ───────────────────────────────────────────────────────
    @staticmethod
    async def list_banks(db: AsyncSession, user_id, currency: Optional[str] = None) -> list[SavedBankAccount]:
        q = select(SavedBankAccount).where(SavedBankAccount.user_id == user_id)
        if currency:
            q = q.where(SavedBankAccount.currency == currency)
        q = q.order_by(SavedBankAccount.created_at.desc())
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def get_bank(db: AsyncSession, account_id, user_id) -> Optional[SavedBankAccount]:
        try:
            aid = uuid.UUID(str(account_id))
        except (ValueError, TypeError):
            return None
        acct = await db.get(SavedBankAccount, aid)
        if not acct or str(acct.user_id) != str(user_id):
            return None
        return acct

    @staticmethod
    async def find_bank(db: AsyncSession, user_id, currency, code, account_number) -> Optional[SavedBankAccount]:
        q = select(SavedBankAccount).where(
            SavedBankAccount.user_id == user_id,
            SavedBankAccount.currency == currency,
            SavedBankAccount.institution_code == code,
            SavedBankAccount.account_number == account_number,
        )
        return (await db.execute(q)).scalars().first()

    @staticmethod
    async def add_bank(db: AsyncSession, user_id, currency, bank_name, code, account_number, account_name, label=None) -> SavedBankAccount:
        existing = await AccountRepository.find_bank(db, user_id, currency, code, account_number)
        if existing:
            return existing
        acct = SavedBankAccount(
            user_id=user_id, currency=currency, bank_name=bank_name,
            institution_code=code, account_number=account_number,
            account_name=account_name, label=label,
        )
        db.add(acct)
        await db.commit()
        await db.refresh(acct)
        return acct

    @staticmethod
    async def delete_bank(db: AsyncSession, account_id, user_id) -> bool:
        acct = await AccountRepository.get_bank(db, account_id, user_id)
        if not acct:
            return False
        await db.delete(acct)
        await db.commit()
        return True

    # ─── Wallets ─────────────────────────────────────────────────────────────
    @staticmethod
    async def list_wallets(db: AsyncSession, user_id) -> list[SavedWallet]:
        q = select(SavedWallet).where(SavedWallet.user_id == user_id).order_by(SavedWallet.created_at.desc())
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def get_wallet(db: AsyncSession, wallet_id, user_id) -> Optional[SavedWallet]:
        try:
            wid = uuid.UUID(str(wallet_id))
        except (ValueError, TypeError):
            return None
        w = await db.get(SavedWallet, wid)
        if not w or str(w.user_id) != str(user_id):
            return None
        return w

    @staticmethod
    async def add_wallet(db: AsyncSession, user_id, address, network, label=None) -> SavedWallet:
        q = select(SavedWallet).where(
            SavedWallet.user_id == user_id,
            SavedWallet.address == address,
            SavedWallet.network == network,
        )
        existing = (await db.execute(q)).scalars().first()
        if existing:
            return existing
        w = SavedWallet(user_id=user_id, address=address, network=network, label=label)
        db.add(w)
        await db.commit()
        await db.refresh(w)
        return w

    @staticmethod
    async def delete_wallet(db: AsyncSession, wallet_id, user_id) -> bool:
        w = await AccountRepository.get_wallet(db, wallet_id, user_id)
        if not w:
            return False
        await db.delete(w)
        await db.commit()
        return True
