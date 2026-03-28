from collections import defaultdict

from exchange_kernel.foundation.clock import format_exchange_time
from exchange_kernel.storage.schema import ExchangeTicket, MarketAsset, QuoteSide, TradePrint


def asset_payload(asset: MarketAsset) -> dict:
    return {"name": asset.name, "ticker": asset.ticker}


def orderbook_payload(tickets: list[ExchangeTicket], side: QuoteSide) -> list[dict]:
    merged: dict[int, int] = defaultdict(int)
    for ticket in tickets:
        merged[ticket.price] += ticket.amount
    return [
        {"price": price, "qty": qty}
        for price, qty in sorted(merged.items(), reverse=(side == QuoteSide.BID))
    ]


def trade_payload(trade: TradePrint) -> dict:
    return {
        "ticker": trade.instrument_ticker,
        "amount": trade.amount,
        "price": trade.price,
        "timestamp": format_exchange_time(trade.timestamp),
    }


def ticket_payload(ticket: ExchangeTicket) -> dict:
    return {
        "id": ticket.id,
        "status": ticket.status.value,
        "user_id": ticket.user_id,
        "timestamp": format_exchange_time(ticket.created_at),
        "body": {
            "direction": "BUY" if ticket.direction == QuoteSide.BID else "SELL",
            "ticker": ticket.instrument_ticker,
            "qty": ticket.amount + ticket.filled,
            "price": ticket.price,
        },
        "filled": ticket.filled,
    }

