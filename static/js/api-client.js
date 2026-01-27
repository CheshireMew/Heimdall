/**
 * API Client for Heimdall
 * Handles all HTTP requests to the backend
 */

// API Base URL (FastAPI on port 5001)
const API_BASE_URL = 'http://localhost:5001/api';

const API = {
    /**
     * 获取系统状态
     */
    async getStatus() {
        try {
            const response = await fetch(`${API_BASE_URL}/status`);
            return await response.json();
        } catch (error) {
            console.error('API Error (getStatus):', error);
            return null;
        }
    },

    /**
     * 获取实时分析数据
     * @param {string} symbol 交易对
     */
    async getRealtime(symbol, timeframe = null) {
        try {
            let url = `${API_BASE_URL}/realtime/${encodeURIComponent(symbol)}`;
            if (timeframe) {
                url += `?timeframe=${timeframe}`;
            }
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('API Error (getRealtime):', error);
            throw error;
        }
    },

    /**
     * 启动回测
     * @param {string} symbol 交易对
     * @param {number} days 回测天数
     * @param {boolean} useAI 是否使用 AI
     */
    async startBacktest(symbol, days, useAI) {
        try {
            const response = await fetch(`${API_BASE_URL}/backtest/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ symbol, days, use_ai: useAI })
            });
            return await response.json();
        } catch (error) {
            console.error('API Error (startBacktest):', error);
            throw error;
        }
    },

    /**
     * 获取回测记录列表
     */
    async getBacktestList() {
        try {
            const response = await fetch(`${API_BASE_URL}/backtest/list`);
            return await response.json();
        } catch (error) {
            console.error('API Error (getBacktestList):', error);
            return [];
        }
    },

    /**
     * 获取回测结果详情
     * @param {number} backtestId 回测ID
     */
    async getBacktestResult(backtestId) {
        try {
            const response = await fetch(`${API_BASE_URL}/backtest/${backtestId}`);
            if (!response.ok) throw new Error('Result not found');
            return await response.json();
        } catch (error) {
            console.error('API Error (getBacktestResult):', error);
            throw error;
        }
    },

    /**
     * 获取市场情绪指数
     */
    async getSentiment() {
        try {
            const response = await fetch(`${API_BASE_URL}/market/sentiment`);
            return await response.json();
        } catch (error) {
            console.error('API Error (getSentiment):', error);
            return null;
        }
    },

    /**
     * 模拟定投 (DCA)
     * @param {string} symbol 交易对
     * @param {number} amount 每日金额
     * @param {string} startDate 开始日期 YYYY-MM-DD
     * @param {string} investmentTime 定投时间 HH:MM
     */
    async simulateDCA(symbol, amount, startDate, investmentTime) {
        try {
            const response = await fetch(`${API_BASE_URL}/tools/dca_simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol,
                    amount,
                    start_date: startDate,
                    investment_time: investmentTime
                })
            });
            return await response.json();
        } catch (error) {
            console.error('API Error (simulateDCA):', error);
            return { error: 'Network Error' };
        }
    },

    /**
     * 获取配置
     */
    async getConfig() {
        try {
            const response = await fetch(`${API_BASE_URL}/config`);
            return await response.json();
        } catch (error) {
            console.error('API Error (getConfig):', error);
            return {};
        }
    },

    /**
     * 币种对比分析
     */
    async comparePairs(symbolA, symbolB, days, timeframe = '1h') {
        try {
            const response = await fetch(`${API_BASE_URL}/tools/compare_pairs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol_a: symbolA,
                    symbol_b: symbolB,
                    days: days,
                    timeframe: timeframe
                })
            });
            return await response.json();
        } catch (error) {
            console.error('API Error (comparePairs):', error);
            throw error;
        }
    }
};
