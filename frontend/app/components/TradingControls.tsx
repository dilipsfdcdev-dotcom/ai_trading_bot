'use client'

import { Play, Pause, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface TradingControlsProps {
  tradingStatus: any
}

export function TradingControls({ tradingStatus }: TradingControlsProps) {
  const [loading, setLoading] = useState(false)

  const handleStartStop = async () => {
    setLoading(true)
    try {
      const endpoint = tradingStatus?.is_active ? '/trading/stop' : '/trading/start'
      await axios.post(`${API_URL}${endpoint}`)
      // Refresh will happen automatically via polling
    } catch (error) {
      console.error('Failed to toggle trading:', error)
      alert('Failed to toggle trading status')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg">
      <h2 className="text-lg font-semibold mb-4">Trading Controls</h2>

      <div className="space-y-3">
        <button
          onClick={handleStartStop}
          disabled={loading}
          className={`w-full px-4 py-3 rounded-lg font-medium flex items-center justify-center space-x-2 transition-colors ${
            tradingStatus?.is_active
              ? 'bg-red-600 hover:bg-red-700 text-white'
              : 'bg-green-600 hover:bg-green-700 text-white'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading ? (
            <RefreshCw className="w-5 h-5 animate-spin" />
          ) : tradingStatus?.is_active ? (
            <>
              <Pause className="w-5 h-5" />
              <span>Stop Trading</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              <span>Start Trading</span>
            </>
          )}
        </button>

        <div className="text-sm text-gray-400 bg-gray-900 rounded-lg p-3 border border-gray-700">
          <p className="font-medium mb-2">Status</p>
          <p>
            {tradingStatus?.is_active
              ? '🟢 Bot is actively scanning and trading'
              : '🔴 Bot is paused'}
          </p>
        </div>
      </div>
    </div>
  )
}
