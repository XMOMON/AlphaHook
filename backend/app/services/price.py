import asyncio
import aiohttp
from app.routers.ws import manager
from app.database import async_session
from app.models.all import Signal, Position, SignalStatus, PositionStatus
from sqlalchemy.future import select

cached_prices = {}

# Map trading pair to CryptoCompare symbol format
# CryptoCompare uses "BTC" not "BTC/USDT", and returns price vs USD
CRYPTO_SYMBOLS = {
    "BTC/USDT": "BTC", "ETH/USDT": "ETH", "BNB/USDT": "BNB",
    "SOL/USDT": "SOL", "XRP/USDT": "XRP", "ADA/USDT": "ADA",
    "DOGE/USDT": "DOGE", "AVAX/USDT": "AVAX", "MATIC/USDT": "MATIC",
    "LINK/USDT": "LINK", "DOT/USDT": "DOT", "SHIB/USDT": "SHIB",
    "LTC/USDT": "LTC", "UNI/USDT": "UNI", "ATOM/USDT": "ATOM",
    "XLM/USDT": "XLM", "VET/USDT": "VET", "FIL/USDT": "FIL",
    "THETA/USDT": "THETA", "XMR/USDT": "XMR", "EOS/USDT": "EOS",
    "AAVE/USDT": "AAVE", "XTZ/USDT": "XTZ", "MKR/USDT": "MKR",
    "BSV/USDT": "BSV", "BCH/USDT": "BCH", "TRX/USDT": "TRX",
    "NEO/USDT": "NEO", "CAKE/USDT": "CAKE", "ALGO/USDT": "ALGO",
    "FTM/USDT": "FTM", "KSM/USDT": "KSM", "DASH/USDT": "DASH",
    "RUNE/USDT": "RUNE", "FEA/USDT": "FEA", "HNT/USDT": "HNT",
    "ENJ/USDT": "ENJ", "MANA/USDT": "MANA", "SAND/USDT": "SAND",
    "APE/USDT": "APE", "GMT/USDT": "GMT", "GALA/USDT": "GALA",
    "ONE/USDT": "ONE", "CHZ/USDT": "CHZ", "ANKR/USDT": "ANKR",
    "IOTA/USDT": "IOTA", "KAVA/USDT": "KAVA", "CRV/USDT": "CRV",
    "SNX/USDT": "SNX",
}

# Reverse: CC symbol -> pair
REVERSE_CRYPTO = {v: k for k, v in CRYPTO_SYMBOLS.items()}

# Forex pairs
FOREX_SYMBOLS = {
    "EUR/USD": ("EUR", "USD"), "USD/JPY": ("USD", "JPY"),
    "GBP/USD": ("GBP", "USD"), "USD/CHF": ("USD", "CHF"),
    "AUD/USD": ("AUD", "USD"), "USD/CAD": ("USD", "CAD"),
    "NZD/USD": ("NZD", "USD"),
}


async def fetch_crypto_prices(session: aiohttp.ClientSession, symbols: list):
    """Fetch crypto prices from CryptoCompare (free, generous rate limit)."""
    if not symbols:
        return {}

    fsyms = ",".join(symbols)
    url = f"https://min-api.cryptocompare.com/data/pricemulti?fsyms={fsyms}&tsyms=USDT"

    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = {}
                for sym, prices in data.items():
                    if "USDT" in prices and sym in REVERSE_CRYPTO:
                        results[REVERSE_CRYPTO[sym]] = prices["USDT"]
                return results
            else:
                print(f"CryptoCompare returned status {resp.status}")
                return {}
    except Exception as e:
        print(f"CryptoCompare fetch error: {e}")
        return {}


async def fetch_forex_prices(session: aiohttp.ClientSession, pairs: list):
    """Fetch forex rates from CryptoCompare (also supports fiat)."""
    if not pairs:
        return {}

    results = {}
    try:
        # Get all major currencies vs USD in one call
        bases = set()
        for pair in pairs:
            if pair in FOREX_SYMBOLS:
                b, q = FOREX_SYMBOLS[pair]
                bases.add(b)
                bases.add(q)
        
        bases.discard("USD")
        if not bases:
            return results

        fsyms = ",".join(bases)
        url = f"https://min-api.cryptocompare.com/data/pricemulti?fsyms={fsyms}&tsyms=USD"

        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                for pair in pairs:
                    if pair in FOREX_SYMBOLS:
                        base, quote = FOREX_SYMBOLS[pair]
                        if base == "USD" and quote in data:
                            # USD/XXX: price = how many XXX per 1 USD
                            # CryptoCompare gives us XXX -> USD, so invert
                            if "USD" in data.get(quote, {}):
                                rate = data[quote]["USD"]
                                if rate > 0:
                                    results[pair] = 1.0 / rate
                        elif base in data and "USD" in data.get(base, {}):
                            # XXX/USD: price = how many USD per 1 XXX
                            results[pair] = data[base]["USD"]
    except Exception as e:
        print(f"Forex fetch error: {e}")

    return results


async def price_polling_loop():
    error_count = 0

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Query active pairs from database
                active_pairs = set()
                async with async_session() as db:
                    result_sig = await db.execute(
                        select(Signal.pair).where(Signal.status == SignalStatus.PENDING)
                    )
                    for pair in result_sig.scalars().all():
                        active_pairs.add(pair)

                    result_pos = await db.execute(
                        select(Position.pair).where(
                            Position.status.in_([PositionStatus.OPEN, PositionStatus.PARTIAL])
                        )
                    )
                    for pair in result_pos.scalars().all():
                        active_pairs.add(pair)

                if active_pairs:
                    crypto_syms = [CRYPTO_SYMBOLS[p] for p in active_pairs if p in CRYPTO_SYMBOLS]
                    forex_pairs = [p for p in active_pairs if p in FOREX_SYMBOLS]

                    crypto_prices, forex_prices = await asyncio.gather(
                        fetch_crypto_prices(session, crypto_syms),
                        fetch_forex_prices(session, forex_pairs),
                    )

                    updated = False
                    for symbol, price in {**crypto_prices, **forex_prices}.items():
                        if price and price > 0:
                            cached_prices[symbol] = price
                            updated = True
                            print(f"  {symbol}: ${price}")

                    if updated:
                        error_count = 0
                        await manager.broadcast({"type": "price_tick", "data": cached_prices})

            except Exception as e:
                error_count += 1
                wait_time = min(error_count * 3, 30)
                print(f"Price poll error (retry in {wait_time}s): {e}")
                await asyncio.sleep(wait_time)
                continue

            await asyncio.sleep(5)


def get_current_price(pair: str) -> float:
    return cached_prices.get(pair, 0.0)
