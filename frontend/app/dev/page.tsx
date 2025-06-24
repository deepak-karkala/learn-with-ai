'use client'

import { useState } from 'react'
import ApiTest from '@/components/dev/ApiTest'

export default function DevPage() {
  if (process.env.NODE_ENV === 'production') {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Development tools not available in production</p>
      </div>
    )
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-8 space-y-8">
      <div className="z-10 max-w-6xl w-full items-center justify-center text-center">
        <h1 className="text-4xl font-bold mb-4">
          Development Tools
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          API testing and development utilities
        </p>
      </div>

      <div className="w-full max-w-4xl">
        <ApiTest />
      </div>
    </main>
  )
}