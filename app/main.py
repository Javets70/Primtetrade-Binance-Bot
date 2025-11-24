import asyncio
import typer
from rich.console import Console
from rich.table import Table
from binance.enums import SIDE_BUY, SIDE_SELL

from app.services.trade_service import TradeService
from app.core.config import settings

app = typer.Typer(
    name="binance-bot", help="Binance Futures Trading Bot CLI", add_completion=False
)
console = Console()


class State:
    def __init__(self):
        self.testnet: bool = True
        self.api_key: str = ""
        self.secret_key: str = ""


state = State()


@app.callback()
def main_callback(
    testnet: bool = typer.Option(
        True, "--testnet/--live", help="Use testnet (True) or live trading (False)"
    ),
    api_key: str | None = typer.Option(
        None,
        envvar="API_KEY",
        help="Binance API Key (or set BINANCE_API_KEY env var)",
    ),
    secret_key: str | None = typer.Option(
        None,
        envvar="SECRET_KEY",
        help="Binance Secret Key (or set BINANCE_SECRET_KEY env var)",
    ),
):
    """
    Binance Futures Trading Bot - CLI Interface

    Configure your API credentials via options or environment variables.
    """
    state.testnet = testnet
    state.api_key = api_key or settings.API_KEY
    state.secret_key = secret_key or settings.SECRET_KEY

    if not state.api_key or not state.secret_key:
        console.print("[red]Error: API credentials not configured[/red]")
        console.print("Set BINANCE_API_KEY and BINANCE_SECRET_KEY env vars")
        raise typer.Exit(code=1)

    mode = "TESTNET" if state.testnet else "LIVE"
    console.print(f"[yellow]Mode: {mode}[/yellow]")


def run_async(coro):
    """Wrapper to run async functions in Typer commands"""
    return asyncio.run(coro)


@app.command("market")
def market_order(
    symbol: str = typer.Argument(..., help="Trading pair (e.g., BTCUSDT)"),
    side: str = typer.Argument(..., help="BUY or SELL"),
    quantity: float = typer.Argument(..., help="Amount to trade"),
):
    """
    Place a MARKET order (executes immediately at current price)

    Example: market BTCUSDT BUY 0.001
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            order = await service.place_futures_market_order(
                symbol=symbol.upper(), side=side.upper(), quantity=quantity
            )

            console.print("\n[green]✓ Market Order Placed Successfully[/green]")
            _display_order(order)

    run_async(execute())


@app.command("limit")
def limit_order(
    symbol: str = typer.Argument(..., help="Trading pair (e.g., BTCUSDT)"),
    side: str = typer.Argument(..., help="BUY or SELL"),
    quantity: float = typer.Argument(..., help="Amount to trade"),
    price: float = typer.Argument(..., help="Limit price"),
):
    """
    Place a LIMIT order (execute at specified price or better)

    Example: limit BTCUSDT BUY 0.001 50000
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            order = await service.place_futures_limit_order(
                symbol=symbol.upper(), side=side.upper(), quantity=quantity, price=price
            )

            console.print("\n[green]✓ Limit Order Placed Successfully[/green]")
            _display_order(order)

    run_async(execute())


@app.command("stop-limit")
def stop_limit_order(
    symbol: str = typer.Argument(..., help="Trading pair (e.g., BTCUSDT)"),
    side: str = typer.Argument(..., help="BUY or SELL"),
    quantity: float = typer.Argument(..., help="Amount to trade"),
    price: float = typer.Argument(..., help="Execution limit price"),
    stop_price: float = typer.Argument(..., help="Trigger stop price"),
):
    """
    Place a STOP-LIMIT order (trigger at stop price, execute at limit price)

    Example: stop-limit BTCUSDT SELL 0.001 44900 45000
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            order = await service.place_stop_limit_order(
                symbol=symbol.upper(),
                side=side.upper(),
                quantity=quantity,
                price=price,
                stop_price=stop_price,
            )

            console.print("\n[green]✓ Stop-Limit Order Placed Successfully[/green]")
            _display_order(order)

    run_async(execute())


@app.command("price")
def get_price(
    symbol: str = typer.Argument(..., help="Trading pair (e.g., BTCUSDT)"),
):
    """
    Get current market price for a symbol

    Example: price BTCUSDT
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            price = await service.get_current_price(symbol.upper())
            console.print(
                f"\n[cyan]{symbol.upper()}:[/cyan] [green]${price:,.2f}[/green]"
            )

    run_async(execute())


@app.command("balance")
def get_balance():
    """
    Get your futures account balance

    Example: balance
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            balance = await service.get_account_balance()
            console.print(
                f"\n[cyan]Account Balance:[/cyan] [green]${balance:,.2f} USDT[/green]"
            )

    run_async(execute())


@app.command("orders")
def list_orders(
    symbol: str | None = typer.Argument(None, help="Trading pair () | None"),
):
    """
    List all open orders (optionally filter by symbol)

    Example: orders BTCUSDT
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            orders = await service.get_open_orders(
                symbol=symbol.upper() if symbol else None
            )

            if not orders:
                console.print("\n[yellow]No open orders found[/yellow]")
                return

            table = Table(title=f"Open Orders ({len(orders)})")
            table.add_column("Order ID", style="cyan")
            table.add_column("Symbol", style="magenta")
            table.add_column("Side", style="yellow")
            table.add_column("Type", style="blue")
            table.add_column("Quantity", style="green")
            table.add_column("Price", style="green")

            for order in orders:
                table.add_row(
                    str(order["orderId"]),
                    order["symbol"],
                    order["side"],
                    order["type"],
                    str(order["origQty"]),
                    str(order.get("price", "N/A")),
                )

            console.print(table)

    run_async(execute())


@app.command("position")
def get_position(
    symbol: str | None = typer.Argument(None, help="Trading pair () | None"),
):
    """
    Get current position information

    Example: position BTCUSDT
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            positions = await service.get_position_info(
                symbol=symbol.upper() if symbol else None
            )

            # Filter out zero positions
            active_positions = [
                p for p in positions if float(p.get("positionAmt", 0)) != 0
            ]

            if not active_positions:
                console.print("\n[yellow]No active positions[/yellow]")
                return

            table = Table(title="Active Positions")
            table.add_column("Symbol", style="cyan")
            table.add_column("Amount", style="yellow")
            table.add_column("Entry Price", style="green")
            table.add_column("Mark Price", style="green")
            table.add_column("PnL", style="magenta")

            for pos in active_positions:
                pnl = float(pos.get("unRealizedProfit", 0))
                pnl_color = "green" if pnl >= 0 else "red"

                table.add_row(
                    pos["symbol"],
                    pos["positionAmt"],
                    pos["entryPrice"],
                    pos["markPrice"],
                    f"[{pnl_color}]${pnl:,.2f}[/{pnl_color}]",
                )

            console.print(table)

    run_async(execute())


@app.command("cancel")
def cancel_order(
    symbol: str = typer.Argument(..., help="Trading pair (e.g., BTCUSDT)"),
    order_id: int = typer.Argument(..., help="Order ID to cancel"),
):
    """
    Cancel an open order

    Example: cancel BTCUSDT 12345678
    """

    async def execute():
        async with TradeService(
            testnet=state.testnet, api_key=state.api_key, secret_key=state.secret_key
        ) as service:
            result = await service.cancel_order(symbol.upper(), order_id)
            console.print(f"\n[green]✓ Order {order_id} canceled successfully[/green]")

    run_async(execute())


def _display_order(order: dict):
    """Display order details in a formatted table"""
    table = Table(title="Order Details")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    key_fields = [
        ("Order ID", "orderId"),
        ("Symbol", "symbol"),
        ("Side", "side"),
        ("Type", "type"),
        ("Quantity", "origQty"),
        ("Price", "price"),
        ("Stop Price", "stopPrice"),
        ("Status", "status"),
    ]

    for label, key in key_fields:
        value = order.get(key, "N/A")
        if value != "N/A":
            table.add_row(label, str(value))

    console.print(table)


if __name__ == "__main__":
    app()
