'use client'

import { FileText, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

interface DecisionLogProps {
  wsData: any
  analyses: any
}

interface LogEntry {
  timestamp: Date
  type: 'analysis' | 'trade' | 'scan' | 'info'
  message: string
  data?: any
}

export function DecisionLog({ wsData, analyses }: DecisionLogProps) {
  const [logs, setLogs] = useState<LogEntry[]>([])

  useEffect(() => {
    if (wsData) {
      const newLog: LogEntry = {
        timestamp: new Date(),
        type: wsData.type || 'info',
        message: getLogMessage(wsData),
        data: wsData.data
      }

      setLogs(prev => [newLog, ...prev].slice(0, 50)) // Keep last 50 logs
    }
  }, [wsData])

  const getLogMessage = (data: any): string => {
    switch (data.type) {
      case 'analysis':
        return `Analysis complete for ${data.data?.symbol}: ${data.data?.final_signal}`
      case 'trade':
        return `Trade executed: ${data.data?.symbol} ${data.data?.order_type} ${data.data?.volume} lots`
      case 'market_scan':
        const symbols = Object.keys(data.data || {})
        return `Market scan completed for ${symbols.join(', ')}`
      default:
        return 'Update received'
    }
  }

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'trade':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'analysis':
        return <FileText className="w-4 h-4 text-blue-500" />
      case 'scan':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />
      default:
        return <FileText className="w-4 h-4 text-gray-500" />
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg h-[calc(100vh-8rem)] flex flex-col">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        <FileText className="w-5 h-5 mr-2 text-yellow-500" />
        Decision Log
      </h2>

      <div className="flex-1 overflow-y-auto space-y-2">
        {logs.length === 0 ? (
          <p className="text-gray-400 text-center py-4">Waiting for updates...</p>
        ) : (
          logs.map((log, index) => (
            <div
              key={index}
              className="bg-gray-900 rounded-lg p-3 border border-gray-700 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-start space-x-3">
                <div className="mt-1">{getLogIcon(log.type)}</div>

                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300">{log.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDistanceToNow(log.timestamp, { addSuffix: true })}
                  </p>

                  {/* Show reasoning for analysis */}
                  {log.type === 'analysis' && log.data?.reasoning_steps && (
                    <details className="mt-2">
                      <summary className="text-xs text-blue-400 cursor-pointer hover:text-blue-300">
                        View Reasoning
                      </summary>
                      <div className="mt-2 space-y-1 text-xs text-gray-400">
                        {log.data.reasoning_steps.map((step: string, i: number) => (
                          <p key={i}>{step}</p>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
