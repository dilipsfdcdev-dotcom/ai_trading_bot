'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react'
import { AccountInfo } from './components/AccountInfo'
import { PositionsList } from './components/PositionsList'
import { AnalysisPanel } from './components/AnalysisPanel'
import { DecisionLog } from './components/DecisionLog'
import { TradingControls } from './components/TradingControls'
import { RiskMetrics } from './components/RiskMetrics'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

export default function Dashboard() {
  const [wsData, setWsData] = useState<any>(null)
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting')

  // Fetch account info
  const { data: accountInfo } = useQuery({
    queryKey: ['account'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/account`)
      return res.data
    },
    refetchInterval: 5000,
  })

  // Fetch positions
  const { data: positions } = useQuery({
    queryKey: ['positions'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/positions`)
      return res.data
    },
    refetchInterval: 3000,
  })

  // Fetch risk metrics
  const { data: riskMetrics } = useQuery({
    queryKey: ['risk'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/risk`)
      return res.data
    },
    refetchInterval: 5000,
  })

  // Fetch analyses
  const { data: analyses } = useQuery({
    queryKey: ['analyses'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/analyses`)
      return res.data
    },
    refetchInterval: 10000,
  })

  // Fetch trading status
  const { data: tradingStatus } = useQuery({
    queryKey: ['trading-status'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/trading/status`)
      return res.data
    },
    refetchInterval: 5000,
  })

  // WebSocket connection
  useEffect(() => {
    let ws: WebSocket | null = null
    let reconnectTimeout: NodeJS.Timeout

    const connect = () => {
      setConnectionStatus('connecting')
      ws = new WebSocket(WS_URL)

      ws.onopen = () => {
        console.log('WebSocket connected')
        setConnectionStatus('connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setWsData(data)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionStatus('disconnected')
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setConnectionStatus('disconnected')
        // Reconnect after 5 seconds
        reconnectTimeout = setTimeout(connect, 5000)
      }
    }

    connect()

    return () => {
      if (ws) {
        ws.close()
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout)
      }
    }
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Activity className="w-8 h-8 text-blue-500" />
              <h1 className="text-2xl font-bold">AI Trading Bot Dashboard</h1>
            </div>

            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                {connectionStatus === 'connected' ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : connectionStatus === 'connecting' ? (
                  <Clock className="w-5 h-5 text-yellow-500 animate-spin" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                <span className="text-sm">
                  {connectionStatus === 'connected' ? 'Live' :
                   connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}
                </span>
              </div>

              {/* Trading Status */}
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                tradingStatus?.is_active
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-gray-700 text-gray-400'
              }`}>
                {tradingStatus?.is_active ? 'Trading Active' : 'Trading Paused'}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Account & Positions */}
          <div className="space-y-6">
            <AccountInfo accountInfo={accountInfo} />
            <RiskMetrics riskMetrics={riskMetrics} />
            <TradingControls tradingStatus={tradingStatus} />
          </div>

          {/* Middle Column - Analysis & Positions */}
          <div className="space-y-6">
            <AnalysisPanel analyses={analyses} />
            <PositionsList positions={positions} />
          </div>

          {/* Right Column - Decision Log */}
          <div>
            <DecisionLog wsData={wsData} analyses={analyses} />
          </div>
        </div>
      </main>
    </div>
  )
}
