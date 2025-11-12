'use client'

import { TrendingUp, TrendingDown, X } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface PositionsListProps {
  positions: any[]
}

export function PositionsList({ positions }: PositionsListProps) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg">
      <h2 className="text-lg font-semibold mb-4">Open Positions ({positions?.length || 0})</h2>

      {!positions || positions.length === 0 ? (
        <p className="text-gray-400 text-center py-4">No open positions</p>
      ) : (
        <div className="space-y-3">
          {positions.map((position: any) => {
            const isBuy = position.order_type === 'BUY'
            const profitColor = position.profit >= 0 ? 'text-green-400' : 'text-red-400'

            return (
              <div
                key={position.ticket}
                className="bg-gray-900 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center space-x-2">
                    {isBuy ? (
                      <TrendingUp className="w-5 h-5 text-green-500" />
                    ) : (
                      <TrendingDown className="w-5 h-5 text-red-500" />
                    )}
                    <div>
                      <p className="font-semibold">{position.symbol}</p>
                      <p className="text-xs text-gray-400">
                        {position.order_type} {position.volume} lots
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <p className={`text-lg font-bold ${profitColor}`}>
                      ${position.profit.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatDistanceToNow(new Date(position.open_time), { addSuffix: true })}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <p className="text-gray-400">Entry</p>
                    <p className="font-medium">{position.entry_price.toFixed(5)}</p>
                  </div>
                  <div>
                    <p className="text-gray-400">Current</p>
                    <p className="font-medium">{position.current_price.toFixed(5)}</p>
                  </div>
                  {position.stop_loss && (
                    <div>
                      <p className="text-gray-400">Stop Loss</p>
                      <p className="font-medium">{position.stop_loss.toFixed(5)}</p>
                    </div>
                  )}
                  {position.take_profit && (
                    <div>
                      <p className="text-gray-400">Take Profit</p>
                      <p className="font-medium">{position.take_profit.toFixed(5)}</p>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
