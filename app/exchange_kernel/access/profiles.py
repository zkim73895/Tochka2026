import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exchange_kernel.storage.schema import AssetLedger, MarketAsset, ProfileKind, TraderProfile


def cast_profile_id(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


async def spawn_profile(
    session: AsyncSession,
    display_name: str,
    role: ProfileKind = ProfileKind.USER,
) -> TraderProfile:
    profile = TraderProfile(name=display_name, role=role)
    session.add(profile)
    assets = (await session.execute(select(MarketAsset))).scalars().all()
    for asset in assets:
        session.add(AssetLedger(owner=profile, asset=asset, quantity=0.0))
    await session.commit()
    await session.refresh(profile)
    return profile


async def fetch_profile(session: AsyncSession, profile_id: uuid.UUID | str) -> TraderProfile | None:
    return await session.get(TraderProfile, cast_profile_id(profile_id))


async def store_api_key(session: AsyncSession, profile: TraderProfile, api_key: str) -> TraderProfile:
    profile.api_key = api_key
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


async def drop_profile(session: AsyncSession, profile: TraderProfile) -> TraderProfile:
    await session.delete(profile)
    await session.commit()
    return profile

