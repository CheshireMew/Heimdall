
/**
 * Chart Manager (Advanced)
 * Uses TradingView Lightweight Charts for professional financial visualization
 */

class ChartManager {
    constructor(canvasId) {
        // Find container instead of canvas, or create a wrapper
        // Lightweight charts attaches to a DIV, not a CANVAS directly in the same way Chart.js does
        // But our HTML has <canvas id="priceChart"></canvas>.
        // We will replace that canvas with a div container dynamically or assume the user provided container.

        this.ctx = document.getElementById(canvasId);

        // Lightweight charts needs a container div
        this.container = document.createElement('div');
        this.container.style.width = '100%';
        this.container.style.height = '400px'; // Default height
        this.container.style.position = 'relative';

        // Replace canvas with container
        if (this.ctx && this.ctx.parentNode) {
            this.ctx.parentNode.replaceChild(this.container, this.ctx);
        }

        // Initialize Chart
        this.chart = LightweightCharts.createChart(this.container, {
            layout: {
                background: { type: 'solid', color: '#1e293b' }, // Dark background matches theme
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#334155' },
                horzLines: { color: '#334155' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            timeScale: {
                borderColor: '#475569',
                timeVisible: true,
                secondsVisible: false,
            },
        });

        // Add Candlestick Series
        this.candleSeries = this.chart.addCandlestickSeries({
            upColor: '#10b981',        // Green
            downColor: '#ef4444',      // Red
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });

        // Add EMA Series (Line)
        this.emaSeries = this.chart.addLineSeries({
            color: '#f59e0b', // Amber/Yellow
            lineWidth: 2,
        });

        // Resize observer
        new ResizeObserver(entries => {
            if (entries.length === 0 || entries[0].target !== this.container) { return; }
            const newRect = entries[0].contentRect;
            this.chart.applyOptions({ height: newRect.height, width: newRect.width });
        }).observe(this.container);

        this.chart.timeScale().fitContent();
    }

    /**
     * Render Method
     * @param {Array} klineData - Full OHLCV data from API: [[ts, o, h, l, c, v], ...]
     * @param {Array} indicators - Optional indicators (not used fully yet)
     */
    render(klineData, indicators) {
        if (!klineData || klineData.length === 0) return;

        // Format data for Lightweight Charts
        // Expected format: { time: '2019-04-11', open: 80.01, high: 96.63, low: 76.6, close: 88.65 }
        // or time as timestamp (seconds)

        const candles = klineData.map(item => {
            return {
                time: item[0] / 1000, // Convert ms to seconds
                open: item[1],
                high: item[2],
                low: item[3],
                close: item[4]
            };
        });

        // Ensure sorted by time
        candles.sort((a, b) => a.time - b.time);

        this.candleSeries.setData(candles);

        // Render EMA if available
        // Note: For real line rendering, we need a history of EMA values. 
        // Currently API might only return latest EMA for 'realtime' or we calculate it on frontend.
        // If we want to verify the graph, we need arrays. 
        // For MVP, lets just set the price data.

        // Fit content
        // this.chart.timeScale().fitContent(); 
        // Do not auto fit every time to allow scrolling, maybe only on first load?
        // Let's keep it static for now, user can scroll.
    }
}
