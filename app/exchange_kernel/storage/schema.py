import uuid
from datetime import datetime
from enum import Enum as NativeEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ExchangeBase(DeclarativeBase):
    pass


class ProfileKind(NativeEnum):
    USER = "user"
    ADMIN = "admin"


class QuoteSide(NativeEnum):
    ASK = "ask"
    BID = "bid"


class TicketState(NativeEnum):
    NEW = "NEW"
    EXECUTED = "EXECUTED"
    PARTIALLY_EXECUTED = "PARTIALLY_EXECUTED"
    CANCELLED = "CANCELLED"


class TraderProfile(ExchangeBase):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[ProfileKind] = mapped_column(Enum(ProfileKind), default=ProfileKind.USER, nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    api_key: Mapped[str | None] = mapped_column(String, nullable=True)

    tickets: Mapped[list["ExchangeTicket"]] = relationship(
        "ExchangeTicket",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    outbound_trades: Mapped[list["TradePrint"]] = relationship(
        "TradePrint",
        foreign_keys="TradePrint.user_from_id",
        back_populates="sender",
    )
    inbound_trades: Mapped[list["TradePrint"]] = relationship(
        "TradePrint",
        foreign_keys="TradePrint.user_to_id",
        back_populates="receiver",
    )
    holdings: Mapped[list["AssetLedger"]] = relationship(
        "AssetLedger",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MarketAsset(ExchangeBase):
    __tablename__ = "instruments"

    ticker: Mapped[str] = mapped_column(String(10), primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    holders: Mapped[list["AssetLedger"]] = relationship(
        "AssetLedger",
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tickets: Mapped[list["ExchangeTicket"]] = relationship(
        "ExchangeTicket",
        back_populates="asset",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    trades: Mapped[list["TradePrint"]] = relationship("TradePrint", back_populates="asset")


class AssetLedger(ExchangeBase):
    __tablename__ = "user_inventories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    instrument_ticker: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("instruments.ticker", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    owner: Mapped[TraderProfile] = relationship("TraderProfile", back_populates="holdings")
    asset: Mapped[MarketAsset] = relationship("MarketAsset", back_populates="holders")


class ExchangeTicket(ExchangeBase):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    instrument_ticker: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("instruments.ticker", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    filled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direction: Mapped[QuoteSide] = mapped_column(Enum(QuoteSide), nullable=False)
    status: Mapped[TicketState] = mapped_column(Enum(TicketState), default=TicketState.NEW, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    owner: Mapped[TraderProfile] = relationship("TraderProfile", back_populates="tickets")
    asset: Mapped[MarketAsset] = relationship("MarketAsset", back_populates="tickets")


class TradePrint(ExchangeBase):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_from_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    user_to_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    instrument_ticker: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("instruments.ticker", ondelete="SET NULL"),
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    sender: Mapped[TraderProfile | None] = relationship(
        "TraderProfile",
        foreign_keys=[user_from_id],
        back_populates="outbound_trades",
    )
    receiver: Mapped[TraderProfile | None] = relationship(
        "TraderProfile",
        foreign_keys=[user_to_id],
        back_populates="inbound_trades",
    )
    asset: Mapped[MarketAsset | None] = relationship("MarketAsset", back_populates="trades")

