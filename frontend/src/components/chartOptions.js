export const chartTextColor = (dark) => (dark ? '#9ca3af' : '#6b7280')

export const chartAxisLineColor = (dark) => (dark ? '#374151' : '#d1d5db')

export const chartSplitLineColor = (dark) => (dark ? '#374151' : '#e5e7eb')

export const categoryAxis = (dark, data, axisLabel = {}) => ({
  type: 'category',
  data,
  axisLabel: { color: chartTextColor(dark), ...axisLabel },
  axisLine: { lineStyle: { color: chartAxisLineColor(dark) } },
})

export const valueAxis = (dark) => ({
  type: 'value',
  axisLabel: { color: chartTextColor(dark) },
  splitLine: { lineStyle: { color: chartSplitLineColor(dark) } },
})

export const chartGrid = ({ top = 16 } = {}) => ({
  left: 16,
  right: 16,
  top,
  bottom: 16,
  containLabel: true,
})
