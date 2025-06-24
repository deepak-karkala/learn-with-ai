'use client'

import { useState } from 'react'
import { apiService } from '@/lib/api'

interface ApiTestProps {
  className?: string
}

export default function ApiTest({ className = '' }: ApiTestProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<{
    endpoint: string
    status: number
    data?: any
    error?: string
    timestamp: string
  }[]>([])

  const testEndpoint = async (name: string, testFn: () => Promise<any>) => {
    setIsLoading(true)
    
    try {
      const result = await testFn()
      const timestamp = new Date().toLocaleTimeString()
      
      setResults(prev => [...prev, {
        endpoint: name,
        status: result.status,
        data: result.data,
        error: result.error,
        timestamp
      }])
    } catch (error) {
      const timestamp = new Date().toLocaleTimeString()
      setResults(prev => [...prev, {
        endpoint: name,
        status: 500,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const runAllTests = async () => {
    setResults([])
    
    // Test root endpoint
    await testEndpoint('Root Endpoint (/)', () => apiService.healthCheck())
    
    // Test health endpoint
    await testEndpoint('Health Endpoint (/health)', () => apiService.healthCheck())
  }

  const clearResults = () => {
    setResults([])
  }

  return (
    <div className={`p-6 border border-gray-200 rounded-lg ${className}`}>
      <h3 className="text-lg font-semibold mb-4">Backend API Connection Test</h3>
      
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">
          Backend URL: <code className="bg-gray-100 px-2 py-1 rounded text-xs">
            {process.env.NEXT_PUBLIC_API_URL}
          </code>
        </p>
      </div>

      <div className="flex gap-2 mb-4">
        <button
          onClick={runAllTests}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {isLoading ? 'Testing...' : 'Test API Connection'}
        </button>
        
        <button
          onClick={clearResults}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          Clear Results
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium">Test Results:</h4>
          {results.map((result, index) => (
            <div
              key={index}
              className={`p-3 rounded border ${
                result.status >= 200 && result.status < 300
                  ? 'border-green-200 bg-green-50'
                  : 'border-red-200 bg-red-50'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-medium">{result.endpoint}</span>
                <span className="text-xs text-gray-500">{result.timestamp}</span>
              </div>
              
              <div className="text-sm">
                <span className={`font-medium ${
                  result.status >= 200 && result.status < 300
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}>
                  Status: {result.status}
                </span>
              </div>

              {result.error && (
                <div className="text-sm text-red-600 mt-1">
                  Error: {result.error}
                </div>
              )}

              {result.data && (
                <details className="mt-2">
                  <summary className="text-xs cursor-pointer text-gray-600">
                    Response Data
                  </summary>
                  <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-auto">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}