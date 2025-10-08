#!/bin/bash

# Proratio Paper Trading Report Generator
# Shows comprehensive trading performance report

CONFIG="proratio_utilities/config/freqtrade/config_dry.json"
USERDIR="user_data"

echo "=============================================="
echo "  Proratio Paper Trading Report"
echo "  Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

# 1. Overall Profit Summary
echo "📊 PROFIT SUMMARY"
echo "──────────────────────────────────────────────"
freqtrade profit --config "$CONFIG" --userdir "$USERDIR" 2>/dev/null || echo "No trades yet"
echo ""

# 2. Performance by Pair
echo "📈 PERFORMANCE BY PAIR"
echo "──────────────────────────────────────────────"
freqtrade performance --config "$CONFIG" --userdir "$USERDIR" 2>/dev/null || echo "No trades yet"
echo ""

# 3. Recent Trades
echo "🔄 RECENT TRADES (Last 10)"
echo "──────────────────────────────────────────────"
freqtrade list-trades --config "$CONFIG" --userdir "$USERDIR" 2>/dev/null | tail -12 || echo "No trades yet"
echo ""

# 4. Open Trades
echo "💼 CURRENTLY OPEN TRADES"
echo "──────────────────────────────────────────────"
freqtrade show_trades --config "$CONFIG" --userdir "$USERDIR" 2>/dev/null || echo "No open trades"
echo ""

# 5. Database Stats
echo "💾 DATABASE STATISTICS"
echo "──────────────────────────────────────────────"
if [ -f "$USERDIR/tradesv3.dryrun.sqlite" ]; then
    total_trades=$(sqlite3 "$USERDIR/tradesv3.dryrun.sqlite" "SELECT COUNT(*) FROM trades;" 2>/dev/null)
    open_trades=$(sqlite3 "$USERDIR/tradesv3.dryrun.sqlite" "SELECT COUNT(*) FROM trades WHERE is_open=1;" 2>/dev/null)
    closed_trades=$(sqlite3 "$USERDIR/tradesv3.dryrun.sqlite" "SELECT COUNT(*) FROM trades WHERE is_open=0;" 2>/dev/null)

    echo "Total trades: $total_trades"
    echo "Open trades: $open_trades"
    echo "Closed trades: $closed_trades"

    # Win rate
    if [ "$closed_trades" -gt 0 ]; then
        winning=$(sqlite3 "$USERDIR/tradesv3.dryrun.sqlite" "SELECT COUNT(*) FROM trades WHERE is_open=0 AND profit_abs > 0;" 2>/dev/null)
        win_rate=$(echo "scale=2; $winning * 100 / $closed_trades" | bc)
        echo "Win rate: ${win_rate}% ($winning wins / $closed_trades trades)"
    fi
else
    echo "No database found (no trades executed yet)"
fi
echo ""

# 6. Quick Actions
echo "=============================================="
echo "  Quick Actions"
echo "=============================================="
echo ""
echo "View live dashboard:"
echo "  → Open http://localhost:8080 in browser"
echo ""
echo "Generate profit chart:"
echo "  → freqtrade plot-profit --config $CONFIG --userdir $USERDIR"
echo "  → Open: $USERDIR/plot/freqtrade-profit-plot.html"
echo ""
echo "Generate trading chart:"
echo "  → freqtrade plot-dataframe --strategy SimpleTestStrategy --pairs BTC/USDT --config $CONFIG --userdir $USERDIR"
echo "  → Open: $USERDIR/plot/freqtrade-plot-BTC_USDT-1h.html"
echo ""
echo "View logs:"
echo "  → tail -f $USERDIR/logs/freqtrade.log"
echo ""
echo "=============================================="
