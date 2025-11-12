'use client'

import { Brain, TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react'

interface AnalysisPanelProps {
  analyses: any
}

export function AnalysisPanel({ analyses }: AnalysisPanelProps) {
  if (!analyses || Object.keys(analyses).length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Brain className="w-5 h-5 mr-2 text-purple-500" />
          Market Analysis
        </h2>
        <p className="text-gray-400 text-center py-4">No analyses available yet</p>
      </div>
    )
  }

  const getSignalIcon = (signal: string) => {
    if (signal.includes('BUY')) return <TrendingUp className="w-5 h-5 text-green-500" />
    if (signal.includes('SELL')) return <TrendingDown className="w-5 h-5 text-red-500" />
    return <Minus className="w-5 h-5 text-gray-500" />
  }

  const getSignalColor = (signal: string) => {
    if (signal.includes('BUY')) return 'text-green-400 bg-green-500/10 border-green-500/30'
    if (signal.includes('SELL')) return 'text-red-400 bg-red-500/10 border-red-500/30'
    return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 shadow-lg">
      <h2 className="text-lg font-semibold mb-4 flex items-center">
        <Brain className="w-5 h-5 mr-2 text-purple-500" />
        Market Analysis
      </h2>

      <div className="space-y-4">
        {Object.entries(analyses).map(([symbol, analysis]: [string, any]) => (
          <div
            key={symbol}
            className="bg-gray-900 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors"
          >
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
              <div>
                <h3 className="text-lg font-bold">{symbol}</h3>
                <p className="text-sm text-gray-400">
                  {new Date(analysis.timestamp).toLocaleTimeString()}
                </p>
              </div>

              <div className="flex items-center space-x-2">
                {getSignalIcon(analysis.final_signal)}
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getSignalColor(analysis.final_signal)}`}>
                  {analysis.final_signal}
                </span>
              </div>
            </div>

            {/* Confidence */}
            <div className="mb-3">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Confidence</span>
                <span className="font-medium">{(analysis.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    analysis.confidence > 0.75 ? 'bg-green-500' :
                    analysis.confidence > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${analysis.confidence * 100}%` }}
                />
              </div>
            </div>

            {/* Summary */}
            <p className="text-sm text-gray-300 mb-3">{analysis.summary}</p>

            {/* Trade Recommendation */}
            {analysis.should_trade && (
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 mb-3">
                <p className="text-sm font-medium text-blue-400 mb-2">Trade Recommendation</p>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {analysis.suggested_entry && (
                    <div>
                      <p className="text-gray-400">Entry</p>
                      <p className="font-medium">{analysis.suggested_entry.toFixed(5)}</p>
                    </div>
                  )}
                  {analysis.suggested_stop_loss && (
                    <div>
                      <p className="text-gray-400">Stop Loss</p>
                      <p className="font-medium">{analysis.suggested_stop_loss.toFixed(5)}</p>
                    </div>
                  )}
                  {analysis.suggested_take_profit && (
                    <div>
                      <p className="text-gray-400">Take Profit</p>
                      <p className="font-medium">{analysis.suggested_take_profit.toFixed(5)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* AI Reasoning */}
            <div className="text-sm">
              <p className="text-gray-400 mb-1">AI Analysis</p>
              <p className="text-gray-300 italic">{analysis.ai_reasoning}</p>
            </div>

            {/* Technical Details */}
            <div className="mt-3 pt-3 border-t border-gray-700">
              <details className="text-sm">
                <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
                  View Details
                </summary>
                <div className="mt-2 space-y-2">
                  {/* Technical Analysis */}
                  <div>
                    <p className="text-gray-400 font-medium">Technical:</p>
                    <p className="text-gray-300">{analysis.technical_analysis?.reasoning}</p>
                  </div>

                  {/* Sentiment */}
                  <div>
                    <p className="text-gray-400 font-medium">Sentiment:</p>
                    <p className="text-gray-300">
                      {analysis.sentiment_analysis?.overall_sentiment}
                      ({analysis.sentiment_analysis?.news_count} news articles)
                    </p>
                  </div>

                  {/* Risk Factors */}
                  {analysis.risk_factors && analysis.risk_factors.length > 0 && (
                    <div>
                      <p className="text-gray-400 font-medium">Risk Factors:</p>
                      <ul className="list-disc list-inside text-gray-300">
                        {analysis.risk_factors.map((risk: string, i: number) => (
                          <li key={i}>{risk}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </details>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
