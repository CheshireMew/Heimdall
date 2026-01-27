/**
 * Heimdall Main Application
 */

// Global State
const state = {
    currentPage: 'realtime',
    symbol: 'BTC/USDT',
    realtimeTimer: null,
    chartManager: null
};

// DOM Elements
const elements = {
    navItems: document.querySelectorAll('.nav-item'),
    pages: document.querySelectorAll('.page'),
    symbolSelect: document.getElementById('symbolSelect'),
    refreshBtn: document.getElementById('refreshBtn'),
    statusDot: document.querySelector('.status-dot'),
    statusText: document.getElementById('statusText'),

    // Realtime Elements
    currentPrice: document.getElementById('currentPrice'),
    priceChange: document.getElementById('priceChange'), // Not implemented in backend yet
    emaValue: document.getElementById('emaValue'),
    rsiValue: document.getElementById('rsiValue'),
    rsiFill: document.getElementById('rsiFill'),
    macdDif: document.getElementById('macdDif'),
    macdDea: document.getElementById('macdDea'),
    macdHist: document.getElementById('macdHist'),
    aiSignal: document.getElementById('aiSignal'),
    aiConfidence: document.getElementById('aiConfidence'),
    aiReasoning: document.getElementById('aiReasoning'),

    // Sentiment Elements
    sentimentValue: document.getElementById('sentimentValue'),
    sentimentLabel: document.getElementById('sentimentLabel'),

    // Backtest Elements
    backtestForm: document.getElementById('backtestForm'),
    backtestList: document.getElementById('backtestList'),
    backtestProgress: document.getElementById('backtestProgress'),

    // Results Elements
    resultsContent: document.getElementById('resultsContent'),
    backToList: document.getElementById('backToList'),

    // DCA Elements (Updated)
    dcaForm: document.getElementById('dcaForm'),
    dcaResult: document.getElementById('dcaResult'),
    dcaResultContainer: document.getElementById('dcaResultContainer'),

    // DCA Stats
    dcaCurrentPrice: document.getElementById('dcaCurrentPrice'),
    dcaAvgPrice: document.getElementById('dcaAvgPrice'),
    dcaRoiValue: document.getElementById('dcaRoiValue'),

    // Details
    dcaInvested: document.getElementById('dcaInvested'),
    dcaValue: document.getElementById('dcaValue'),
    dcaCoins: document.getElementById('dcaCoins'),

    // Pair Comparison Elements
    compareForm: document.getElementById('compareForm'),
    compareChartContainer: document.getElementById('compareChartContainer'),

    // Settings Elements
    settingsInfo: {
        exchange: document.getElementById('settingsExchange'),
        timeframe: document.getElementById('settingsTimeframe'),
        ai: document.getElementById('settingsAI'),
        ema: document.getElementById('settingsEMA'),
        rsi: document.getElementById('settingsRSI'),
        macdFast: document.getElementById('settingsMACDFast'),
        macdSlow: document.getElementById('settingsMACDSlow'),
    }
};

// Initialize Chart
state.chartManager = new ChartManager('priceChart');

// Navigation Logic
function switchPage(pageId) {
    state.currentPage = pageId;

    // Update Nav
    elements.navItems.forEach(item => {
        if (item.dataset.page === pageId) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Update Pages
    elements.pages.forEach(page => {
        if (page.id === `page-${pageId}`) {
            page.classList.add('active');
        } else {
            page.classList.remove('active');
        }
    });

    // Page specific init
    if (pageId === 'realtime') {
        startRealtimeUpdates();
    } else {
        stopRealtimeUpdates();
    }

    if (pageId === 'backtest') {
        loadBacktestList();
    }

    if (pageId === 'settings') {
        loadSettings();
    }

    if (pageId === 'tools') {
        updateSentiment();
        updateDCACurrentPrice(document.getElementById('dcaSymbol').value);
    }
}

// Event Listeners
elements.navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const pageId = item.dataset.page;
        switchPage(pageId);
    });
});

elements.symbolSelect.addEventListener('change', (e) => {
    state.symbol = e.target.value;
    updateRealtimeData();
});

elements.refreshBtn.addEventListener('click', () => {
    updateRealtimeData();
});

// Update DCA Price on Symbol Change (if on tools page or generally)
document.getElementById('dcaSymbol').addEventListener('change', (e) => {
    updateDCACurrentPrice(e.target.value);
});

async function updateDCACurrentPrice(symbol) {
    if (!elements.dcaCurrentPrice) return;
    elements.dcaCurrentPrice.innerText = 'Loading...';
    try {
        // Fetch 5m data specifically
        const data = await API.getRealtime(symbol, '5m');
        if (data && data.current_price) {
            elements.dcaCurrentPrice.innerText = '$' + data.current_price.toLocaleString();
        }
    } catch (e) {
        console.error('Failed to update DCA price', e);
        elements.dcaCurrentPrice.innerText = '--';
    }
}

// Backtest Form
elements.backtestForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const symbol = document.getElementById('btSymbol').value;
    const days = parseInt(document.getElementById('btDays').value);
    const useAI = document.getElementById('btUseAI').checked;

    if (days < 1 || days > 30) {
        alert('回测天数必须在 1-30 之间');
        return;
    }

    // Show Loading
    elements.backtestProgress.classList.remove('hidden');
    elements.backtestForm.querySelector('button').disabled = true;

    try {
        const result = await API.startBacktest(symbol, days, useAI);
        if (result.success) {
            alert('回测成功完成！');
            loadBacktestList(); // Refresh list
        } else {
            alert('回测失败: ' + result.error);
        }
    } catch (error) {
        alert('请求出错');
    } finally {
        elements.backtestProgress.classList.add('hidden');
        elements.backtestForm.querySelector('button').disabled = false;
    }
});

elements.backToList.addEventListener('click', () => {
    switchPage('backtest');
});

// DCA Simulator Form
if (elements.dcaForm) {
    let roiChartInstance = null;
    let costChartInstance = null;

    // Set default date to 1 year ago
    const today = new Date();
    const lastYear = new Date(today);
    lastYear.setFullYear(today.getFullYear() - 1);
    const dateStr = lastYear.toISOString().split('T')[0];
    const dateInput = document.getElementById('dcaStartDate');
    if (dateInput) {
        dateInput.value = dateStr;
    }

    elements.dcaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const symbol = document.getElementById('dcaSymbol').value;
        const startDate = document.getElementById('dcaStartDate').value;
        const time = document.getElementById('dcaTime').value;
        const amount = parseFloat(document.getElementById('dcaAmount').value);

        if (!startDate) {
            alert('请选择开始日期');
            return;
        }

        const btn = e.target.querySelector('button');
        const originalText = btn.innerText;
        btn.disabled = true;
        btn.innerText = '计算中...';

        try {
            const result = await API.simulateDCA(symbol, amount, startDate, time);

            if (result.error) {
                alert('计算失败: ' + result.error);
                return;
            }

            // 1. Top Stats
            // Refresh Live Price (5m close)
            updateDCACurrentPrice(symbol);
            // elements.dcaCurrentPrice.innerText = ... (Handled by updateDCACurrentPrice)
            elements.dcaAvgPrice.innerText = '$' + result.average_price.toFixed(2);

            const roi = result.roi_percent;
            elements.dcaRoiValue.innerText = (roi >= 0 ? '+' : '') + roi.toFixed(2) + '%';
            elements.dcaRoiValue.style.color = roi >= 0 ? '#10b981' : '#ef4444';

            // Refresh Sentiment (Now displayed here)
            updateSentiment();

            // 2. Details
            elements.dcaInvested.innerText = '$' + result.total_invested.toLocaleString();
            elements.dcaValue.innerText = '$' + result.final_value.toLocaleString();
            elements.dcaCoins.innerText = result.total_coins.toFixed(4) + ' ' + symbol.split('/')[0];

            // 3. Render ROI Chart (Solid Line)
            const ctxRoi = document.getElementById('dcaRoiChart').getContext('2d');
            if (roiChartInstance) roiChartInstance.destroy();

            roiChartInstance = new Chart(ctxRoi, {
                type: 'line',
                data: {
                    labels: result.labels,
                    datasets: [{
                        label: '收益率 (ROI %)',
                        data: result.roi_curve,
                        // Remove fixed colors, use segment
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        tension: 0.1,
                        segment: {
                            borderColor: ctx => ctx.p0.parsed.y >= 0 ? '#10b981' : '#ef4444',
                            backgroundColor: ctx => ctx.p0.parsed.y >= 0 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'
                        }
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { grid: { color: '#334155' }, ticks: { maxTicksLimit: 8 } },
                        y: {
                            grid: { color: '#334155' },
                            ticks: { callback: (val) => val + '%' }
                        }
                    }
                }
            });

            // 4. Render Price vs Cost Chart
            const ctxCost = document.getElementById('dcaCostChart').getContext('2d');
            if (costChartInstance) costChartInstance.destroy();

            costChartInstance = new Chart(ctxCost, {
                type: 'line',
                data: {
                    labels: result.labels,
                    datasets: [
                        {
                            label: '币价 (Price)',
                            data: result.price_curve,
                            borderColor: '#ffffff', // Bright white for visibility
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false
                        },
                        {
                            label: '平均成本 (Avg Cost)',
                            data: result.cost_curve,
                            borderColor: '#f59e0b', // Yellow/Warning color
                            borderWidth: 3,
                            pointRadius: 0,
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: { legend: { position: 'top' } },
                    scales: {
                        x: { grid: { color: '#334155' }, ticks: { maxTicksLimit: 8 } },
                        y: { grid: { color: '#334155' } }
                    }
                }
            });

        } catch (error) {
            alert('请求出错');
            console.error(error);
        } finally {
            btn.disabled = false;
            btn.innerText = originalText;
        }
    });
}

// --- Realtime Logic ---

function startRealtimeUpdates() {
    updateSentiment();
    updateRealtimeData();
    // Poll every 30 seconds
    if (state.realtimeTimer) clearInterval(state.realtimeTimer);
    state.realtimeTimer = setInterval(() => {
        updateRealtimeData();
    }, 30000);
}

function stopRealtimeUpdates() {
    if (state.realtimeTimer) clearInterval(state.realtimeTimer);
}

async function updateSentiment() {
    // Only if element exists (now on DCA page)
    if (!elements.sentimentValue) return;

    try {
        const data = await API.getSentiment();
        if (data && data.value) {
            elements.sentimentValue.innerText = data.value;

            // Translation Map
            const map = {
                'Extreme Fear': '极度恐惧',
                'Fear': '恐惧',
                'Neutral': '中性',
                'Greed': '贪婪',
                'Extreme Greed': '极度贪婪'
            };
            const labelEn = data.value_classification;
            const labelCn = map[labelEn] || labelEn;

            elements.sentimentLabel.innerText = labelCn;

            // Color mapping
            const val = parseInt(data.value);
            let color = '#f59e0b';
            if (val <= 25) color = '#ef4444'; // Extreme Fear
            else if (val >= 75) color = '#10b981'; // Extreme Greed
            else if (val >= 50) color = '#3b82f6'; // Greed / Neutral

            elements.sentimentValue.style.color = color;
        }
    } catch (e) {
        console.error('Sentiment Error', e);
    }
}

async function updateRealtimeData() {
    elements.statusText.innerText = '获取数据中...';
    elements.statusDot.classList.remove('connected');

    try {
        const data = await API.getRealtime(state.symbol);

        // Update UI
        elements.currentPrice.innerText = data.current_price.toFixed(2);

        // Indicators
        const indicators = data.indicators;
        if (indicators.ema) elements.emaValue.innerText = indicators.ema.toFixed(2);
        if (indicators.rsi) {
            elements.rsiValue.innerText = indicators.rsi.toFixed(2);
            elements.rsiFill.style.width = `${indicators.rsi}%`;
            // Color based on RSI
            if (indicators.rsi > 70) elements.rsiFill.style.backgroundColor = '#ef4444'; // Red
            else if (indicators.rsi < 30) elements.rsiFill.style.backgroundColor = '#10b981'; // Green
            else elements.rsiFill.style.backgroundColor = '#3b82f6'; // Blue
        }

        if (indicators.macd) {
            elements.macdDif.innerText = indicators.macd.dif ? indicators.macd.dif.toFixed(4) : '--';
            elements.macdDea.innerText = indicators.macd.dea ? indicators.macd.dea.toFixed(4) : '--';
            elements.macdHist.innerText = indicators.macd.histogram ? indicators.macd.histogram.toFixed(4) : '--';
        }

        // AI Analysis
        if (data.ai_analysis) {
            elements.aiSignal.innerText = data.ai_analysis.signal;
            elements.aiConfidence.innerText = data.ai_analysis.confidence + '%';
            elements.aiReasoning.innerText = data.ai_analysis.reasoning;

            // Colorize Signal
            elements.aiSignal.style.color = data.ai_analysis.signal === 'BUY' ? '#10b981' : (data.ai_analysis.signal === 'SELL' ? '#ef4444' : '#f59e0b');
        }

        // Update Chart
        const klineData = data.kline_data;
        // Pass full kline data to new Lightweight Chart Manager
        state.chartManager.render(klineData, data.indicators);

        elements.statusText.innerText = '已更新';
        elements.statusDot.classList.add('connected');

    } catch (error) {
        elements.statusText.innerText = '连接失败';
        elements.statusDot.classList.remove('connected');
    }
}

// --- Backtest Logic ---

async function loadBacktestList() {
    elements.backtestList.innerHTML = '<p style="text-align:center; padding:1rem;">加载中...</p>';
    const list = await API.getBacktestList();

    if (!list || list.length === 0) {
        elements.backtestList.innerHTML = '<p class="empty-state">暂无回测记录</p>';
        return;
    }

    let html = '';
    list.forEach(item => {
        let statusClass = item.status === 'completed' ? 'success' : (item.status === 'failed' ? 'danger' : 'warning');

        html += `
            <div class="card result-item" style="margin-bottom: 1rem; cursor: pointer; border-left: 4px solid var(--${statusClass})" onclick="viewBacktestResult(${item.id})">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h4 style="font-size:1.1rem; margin-bottom:0.25rem;">${item.symbol} (${item.timeframe})</h4>
                        <span style="font-size:0.85rem; color:#94a3b8;">${new Date(item.created_at).toLocaleString()}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:1.2rem; font-weight:700;">${item.total_signals} <span style="font-size:0.8rem; font-weight:400;">信号</span></div>
                        <span style="font-size:0.85rem; color:var(--${statusClass}); text-transform:uppercase;">${item.status}</span>
                    </div>
                </div>
            </div>
        `;
    });

    elements.backtestList.innerHTML = html;
}

window.viewBacktestResult = async (id) => {
    switchPage('results');
    elements.resultsContent.innerHTML = '<p style="text-align:center; padding:2rem;">加载详情中...</p>';

    try {
        const result = await API.getBacktestResult(id);

        // Render Details
        let signalsHtml = '';
        if (result.signals && result.signals.length > 0) {
            signalsHtml = '<div style="display:grid; gap:1rem; margin-top:2rem;">';
            result.signals.forEach((sig, index) => {
                let color = sig.signal === 'BUY' ? '#10b981' : '#ef4444';
                signalsHtml += `
                    <div class="card" style="border-left: 4px solid ${color}">
                        <div style="display:flex; justify-content:space-between;">
                            <strong>#${index + 1} ${sig.signal}</strong>
                            <span>${new Date(sig.timestamp).toLocaleString()}</span>
                        </div>
                        <div style="margin-top:0.5rem;">价格: ${sig.price} | 置信度: ${sig.confidence}%</div>
                        ${sig.reasoning ? `<div style="margin-top:0.5rem; font-size:0.9rem; color:#ccc;">${sig.reasoning}</div>` : ''}
                    </div>
                 `;
            });
            signalsHtml += '</div>';
        } else {
            signalsHtml = '<p class="empty-state">本次回测未产生交易信号</p>';
        }

        elements.resultsContent.innerHTML = `
            <div class="card">
                <h3>回测报告: ${result.symbol}</h3>
                <div class="settings-info" style="margin-bottom:0;">
                    <div class="info-item"><span class="info-label">K线数量</span><span class="info-value">${result.total_candles}</span></div>
                    <div class="info-item"><span class="info-label">总信号</span><span class="info-value">${result.total_signals}</span></div>
                    <div class="info-item"><span class="info-label">BUY</span><span class="info-value" style="color:var(--success)">${result.buy_signals}</span></div>
                    <div class="info-item"><span class="info-label">SELL</span><span class="info-value" style="color:var(--danger)">${result.sell_signals}</span></div>
                </div>
            </div>
            ${signalsHtml}
        `;

    } catch (error) {
        elements.resultsContent.innerHTML = '<p class="empty-state" style="color:var(--danger)">加载失败</p>';
    }
};

// --- Pair Comparison Logic ---

if (elements.compareForm) {
    // 缓存原始数据和图表实例
    let cachedData = null;
    let comparisonChartInstances = null;
    let currentTimeframe = '1h';

    elements.compareForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const symbolA = document.getElementById('symbolA').value.toUpperCase().trim();
        const symbolB = document.getElementById('symbolB').value.toUpperCase().trim();

        if (!symbolA || !symbolB) {
            alert('请输入两个币种符号');
            return;
        }

        const btn = e.target.querySelector('button');
        const originalText = btn.innerText;
        btn.disabled = true;
        btn.innerText = '加载中...';

        try {
            // 固定获取30天的5分钟数据
            const result = await API.comparePairs(symbolA, symbolB, 30, '5m');

            console.log('API Response:', result);

            if (result.error) {
                alert('对比失败: ' + result.error);
                btn.disabled = false;
                btn.innerText = originalText;
                return;
            }

            // 缓存原始5分钟数据
            cachedData = {
                symbolA: result.symbol_a,
                symbolB: result.symbol_b,
                ratioSymbol: result.ratio_symbol,
                data5m_a: result.data_a,
                data5m_b: result.data_b,
                ratio5m: result.ratio_ohlc
            };

            console.log('Cached 5m data:', {
                data_a: cachedData.data5m_a.length,
                data_b: cachedData.data5m_b.length,
                ratio: cachedData.ratio5m.length
            });

            // 显示周期切换器
            document.getElementById('timeframeSwitcher').style.display = 'flex';

            // 渲染默认周期（1h）
            renderCharts(currentTimeframe);

        } catch (error) {
            console.error('Comparison error:', error);
            alert('请求出错: ' + error.message);
        } finally {
            btn.disabled = false;
            btn.innerText = originalText;
        }
    });

    // 周期切换按钮事件
    document.querySelectorAll('.timeframe-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (!cachedData) {
                alert('请先加载数据');
                return;
            }

            const timeframe = btn.dataset.tf;
            currentTimeframe = timeframe;

            // 更新按钮状态
            document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 重新渲染图表
            renderCharts(timeframe);
        });
    });

    // 渲染图表函数
    function renderCharts(timeframe) {
        console.log(`Rendering charts with timeframe: ${timeframe}`);

        // 聚合数据
        const aggregatedA = aggregateKlines(cachedData.data5m_a, timeframe);
        const aggregatedB = aggregateKlines(cachedData.data5m_b, timeframe);
        const aggregatedRatio = aggregateKlines(cachedData.ratio5m, timeframe);

        console.log('Aggregated data:', {
            data_a: aggregatedA.length,
            data_b: aggregatedB.length,
            ratio: aggregatedRatio.length
        });

        // 更新标题
        document.getElementById('compareTitle').innerText =
            `${cachedData.symbolA} vs ${cachedData.symbolB} (${cachedData.ratioSymbol}) - ${timeframe.toUpperCase()}`;

        // 清理旧图表
        if (comparisonChartInstances) {
            comparisonChartInstances.remove();
            comparisonChartInstances = null;
        }

        // 创建新的图表容器
        const container = document.getElementById('comparisonChart');
        container.innerHTML = '';
        container.style.display = 'flex';
        container.style.gap = '10px';

        // 左侧：比值图
        const leftPanel = document.createElement('div');
        leftPanel.style.flex = '1';
        leftPanel.style.display = 'flex';
        leftPanel.style.flexDirection = 'column';
        leftPanel.style.height = '100%';

        const chartRatioDiv = document.createElement('div');
        chartRatioDiv.style.flex = '1';
        chartRatioDiv.style.minHeight = '400px';
        chartRatioDiv.id = 'chartRatioContainer';

        leftPanel.appendChild(chartRatioDiv);

        // 右侧：两个币种图
        const rightPanel = document.createElement('div');
        rightPanel.style.flex = '1';
        rightPanel.style.display = 'flex';
        rightPanel.style.flexDirection = 'column';
        rightPanel.style.gap = '10px';
        rightPanel.style.height = '100%';

        const chartADiv = document.createElement('div');
        chartADiv.style.flex = '1';
        chartADiv.style.minHeight = '195px';
        chartADiv.id = 'chartAContainer';

        const chartBDiv = document.createElement('div');
        chartBDiv.style.flex = '1';
        chartBDiv.style.minHeight = '195px';
        chartBDiv.id = 'chartBContainer';

        rightPanel.appendChild(chartADiv);
        rightPanel.appendChild(chartBDiv);

        container.appendChild(leftPanel);
        container.appendChild(rightPanel);

        // 检查 LightweightCharts
        if (typeof LightweightCharts === 'undefined') {
            console.error('LightweightCharts 未加载！');
            alert('图表库未加载，请刷新页面重试');
            return;
        }

        // 创建三个K线图
        const chartA = LightweightCharts.createChart(chartADiv, {
            layout: { background: { color: '#0f172a' }, textColor: '#f1f5f9' },
            grid: { vertLines: { color: '#334155' }, horzLines: { color: '#334155' } },
            timeScale: { timeVisible: true, secondsVisible: false }
        });

        const seriesA = chartA.addCandlestickSeries({
            upColor: '#10b981', downColor: '#ef4444',
            borderVisible: false, wickUpColor: '#10b981', wickDownColor: '#ef4444'
        });
        seriesA.setData(aggregatedA);

        const chartB = LightweightCharts.createChart(chartBDiv, {
            layout: { background: { color: '#0f172a' }, textColor: '#f1f5f9' },
            grid: { vertLines: { color: '#334155' }, horzLines: { color: '#334155' } },
            timeScale: { timeVisible: true, secondsVisible: false }
        });

        const seriesB = chartB.addCandlestickSeries({
            upColor: '#10b981', downColor: '#ef4444',
            borderVisible: false, wickUpColor: '#10b981', wickDownColor: '#ef4444'
        });
        seriesB.setData(aggregatedB);

        const chartRatio = LightweightCharts.createChart(chartRatioDiv, {
            layout: { background: { color: '#0f172a' }, textColor: '#f1f5f9' },
            grid: { vertLines: { color: '#334155' }, horzLines: { color: '#334155' } },
            timeScale: { timeVisible: true, secondsVisible: false }
        });

        const seriesRatio = chartRatio.addCandlestickSeries({
            upColor: '#3b82f6', downColor: '#f59e0b',
            borderVisible: false, wickUpColor: '#3b82f6', wickDownColor: '#f59e0b'
        });
        seriesRatio.setData(aggregatedRatio);

        // 初始化时间范围（显示最近的数据）
        chartA.timeScale().fitContent();
        chartB.timeScale().fitContent();
        chartRatio.timeScale().fitContent();

        // **核心功能1：三图时间轴联动**
        let isSyncing = false; // 防止递归同步

        const syncTimeScales = (sourceChart, targetCharts) => {
            const timeScale = sourceChart.timeScale();
            timeScale.subscribeVisibleLogicalRangeChange(() => {
                if (isSyncing) return;

                isSyncing = true;
                const logicalRange = timeScale.getVisibleLogicalRange();
                if (logicalRange) {
                    targetCharts.forEach(chart => {
                        chart.timeScale().setVisibleLogicalRange(logicalRange);
                    });
                }
                isSyncing = false;
            });
        };

        // 设置双向同步
        syncTimeScales(chartA, [chartB, chartRatio]);
        syncTimeScales(chartB, [chartA, chartRatio]);
        syncTimeScales(chartRatio, [chartA, chartB]);

        // **核心功能2：动态加载更多数据（TODO：需要后端支持）**
        // 当用户滚动到边界时，提示加载更多
        const checkBoundary = (chart, chartName) => {
            chart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
                if (!range) return;

                // 检查是否接近左边界（历史数据）
                if (range.from < 10) {
                    console.log(`${chartName}: 接近左边界，可加载更多历史数据`);
                    // TODO: 实现加载更多数据的逻辑
                    // 目前已固定加载30天5m数据，基本够用
                }
            });
        };

        checkBoundary(chartRatio, 'Ratio Chart');

        comparisonChartInstances = {
            remove: () => {
                chartA.remove();
                chartB.remove();
                chartRatio.remove();
            }
        };

        console.log('Charts rendered with sync enabled');
    }

    // 前端K线聚合函数
    function aggregateKlines(klines, timeframe) {
        const tfMinutes = {
            '5m': 5, '15m': 15, '30m': 30, '1h': 60,
            '4h': 240, '1d': 1440, '1w': 10080, '1M': 43200
        };

        if (timeframe === '5m' || !tfMinutes[timeframe]) {
            return klines; // 无需聚合
        }

        const intervalSeconds = tfMinutes[timeframe] * 60;
        const aggregated = [];
        let currentBucket = null;

        for (const kline of klines) {
            const bucketStart = Math.floor(kline.time / intervalSeconds) * intervalSeconds;

            if (!currentBucket || currentBucket.time !== bucketStart) {
                if (currentBucket) aggregated.push(currentBucket);
                currentBucket = {
                    time: bucketStart,
                    open: kline.open,
                    high: kline.high,
                    low: kline.low,
                    close: kline.close
                };
            } else {
                currentBucket.high = Math.max(currentBucket.high, kline.high);
                currentBucket.low = Math.min(currentBucket.low, kline.low);
                currentBucket.close = kline.close;
            }
        }

        if (currentBucket) aggregated.push(currentBucket);
        return aggregated;
    }
}

// --- Settings Logic ---

async function loadSettings() {
    const config = await API.getConfig();

    elements.settingsInfo.exchange.innerText = config.exchange;
    elements.settingsInfo.timeframe.innerText = config.timeframe;
    elements.settingsInfo.ai.innerText = config.exchange ? '已配置' : '未配置'; // Simplified check

    if (config.indicators) {
        elements.settingsInfo.ema.innerText = config.indicators.ema_period;
        elements.settingsInfo.rsi.innerText = config.indicators.rsi_period;
        elements.settingsInfo.macdFast.innerText = config.indicators.macd_fast;
        elements.settingsInfo.macdSlow.innerText = config.indicators.macd_slow;
    }
}

// Init
loadSettings();
switchPage('realtime');
