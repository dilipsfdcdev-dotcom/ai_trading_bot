'use client'

import { Shield, AlertTriangle } from 'lucide-react'

interface RiskMetricsProps {
  riskMetrics: any
}

export function RiskMetrics({ riskMetrics }: RiskMetricsProps) {
  if (!riskMetrics) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-lg font-semibold mb-4">Risk Metrics</h2>
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  const dailyPnLColor = riskMetrics.daily_pnl >= 0 ? 'text-green-400' : 'text-red-400'
  const drawdownColor = riskMetrics.current_drawdown > 10 ? 'text-red-400' :
                       riskMetrics.current_drawdown > 5 ? 'text-yellow-400' : 'text-green-400'

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        <Shield className="w-5 h-5 mr-2 text-green-500" />
        Risk Metrics
      </h2>

      <div className="space-y-4">
        {/* Positions */}
        <div>
          <p className="text-sm text-gray-400">Open Positions</p>
          <div className="flex items-center justify-between">
            <p className="text-2xl font-bold">
              {riskMetrics.open_positions} / {riskMetrics.max_positions}
            </p>
            <div className="text-sm">
              {riskMetrics.can_trade ? (
                <span className="text-green-400">✓ Can Trade</span>
              ) : (
                <span className="text-red-400">✗ Blocked</span>
              )}
            </div>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
            <div
              className="bg-blue-500 h-2 rounded-full"
              style={{
                width: `${(riskMetrics.open_positions / riskMetrics.max_positions) * 100}%`
              }}
            />
          </div>
        </div>

        {/* Daily P&L */}
        <div>
          <p className="text-sm text-gray-400">Daily P&L</p>
          <div className={`text-xl font-bold ${dailyPnLColor}`}>
            ${riskMetrics.daily_pnl?.toFixed(2) || '0.00'}
            <span className="text-sm ml-2">
              ({riskMetrics.daily_pnl_percent?.toFixed(2) || '0.00'}%)
            </span>
          </div>
        </div>

        {/* Drawdown */}
        <div>
          <p className="text-sm text-gray-400">Current Drawdown</p>
          <p className={`text-xl font-bold ${drawdownColor}`}>
            {riskMetrics.current_drawdown?.toFixed(2) || '0.00'}%
          </p>
          {riskMetrics.current_drawdown > 10 && (
            <div className="flex items-center mt-1 text-yellow-400 text-sm">
              <AlertTriangle className="w-4 h-4 mr-1" />
              <span>High drawdown warning</span>
            </div>
          )}
        </div>

        {/* Additional Metrics */}
        <div className="pt-4 border-t border-gray-700 space-y-2">
          {riskMetrics.balance && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Balance</span>
              <span className="font-medium">${riskMetrics.balance.toFixed(2)}</span>
            </div>
          )}
          {riskMetrics.equity && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Equity</span>
              <span className="font-medium">${riskMetrics.equity.toFixed(2)}</span>
            </div>
          )}
          {riskMetrics.free_margin && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Free Margin</span>
              <span className="font-medium">${riskMetrics.free_margin.toFixed(2)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
