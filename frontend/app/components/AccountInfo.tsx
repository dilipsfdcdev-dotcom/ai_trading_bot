'use client'

import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react'

interface AccountInfoProps {
  accountInfo: any
}

export function AccountInfo({ accountInfo }: AccountInfoProps) {
  if (!accountInfo) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-lg font-semibold mb-4">Account Information</h2>
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  const profitColor = accountInfo.profit >= 0 ? 'text-green-400' : 'text-red-400'
  const profitIcon = accountInfo.profit >= 0 ? TrendingUp : TrendingDown

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        <DollarSign className="w-5 h-5 mr-2 text-blue-500" />
        Account Information
      </h2>

      <div className="space-y-4">
        {/* Balance */}
        <div>
          <p className="text-sm text-gray-400">Balance</p>
          <p className="text-2xl font-bold">${accountInfo.balance.toFixed(2)}</p>
        </div>

        {/* Equity */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400">Equity</p>
            <p className="text-lg font-semibold">${accountInfo.equity.toFixed(2)}</p>
          </div>

          <div>
            <p className="text-sm text-gray-400">Free Margin</p>
            <p className="text-lg font-semibold">${accountInfo.free_margin.toFixed(2)}</p>
          </div>
        </div>

        {/* Profit/Loss */}
        <div>
          <p className="text-sm text-gray-400">Current P&L</p>
          <div className={`text-xl font-bold flex items-center ${profitColor}`}>
            {React.createElement(profitIcon, { className: 'w-5 h-5 mr-2' })}
            ${accountInfo.profit.toFixed(2)}
          </div>
        </div>

        {/* Additional Info */}
        <div className="pt-4 border-t border-gray-700 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Leverage</span>
            <span className="font-medium">1:{accountInfo.leverage}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Server</span>
            <span className="font-medium">{accountInfo.server}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Currency</span>
            <span className="font-medium">{accountInfo.currency}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
