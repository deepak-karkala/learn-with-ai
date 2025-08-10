'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface AuthUIProps {
    onAuthenticated: () => void
}

export function AuthUI({ onAuthenticated }: AuthUIProps) {
    const [isSignup, setIsSignup] = useState(false)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError(null)

        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000))

            // Mock authentication - accept any non-empty credentials
            if (email.trim() && password.trim() && (isSignup ? name.trim() : true)) {
                onAuthenticated()
            } else {
                setError('Please fill in all required fields')
            }
        } catch (err) {
            setError('Authentication failed. Please try again.')
        } finally {
            setIsLoading(false)
        }
    }

    const resetForm = () => {
        setEmail('')
        setPassword('')
        setName('')
        setError(null)
    }

    return (
        <Card className="w-full max-w-md mx-auto">
            <CardHeader className="pb-3">
                <CardTitle className="flex items-center justify-between">
                    {isSignup ? 'Create Account' : 'Sign In'}
                    <Badge variant="outline">
                        {isSignup ? 'Sign Up' : 'Login'}
                    </Badge>
                </CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {isSignup && (
                        <div>
                            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                                Full Name
                            </label>
                            <Input
                                id="name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Enter your full name"
                                required={isSignup}
                                disabled={isLoading}
                            />
                        </div>
                    )}

                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                            Email
                        </label>
                        <Input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email"
                            required
                            disabled={isLoading}
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                            Password
                        </label>
                        <Input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                            disabled={isLoading}
                        />
                    </div>

                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-md p-3">
                            <div className="text-sm text-red-800">{error}</div>
                        </div>
                    )}

                    <Button
                        type="submit"
                        className="w-full"
                        disabled={isLoading}
                    >
                        {isLoading
                            ? (isSignup ? 'Creating Account...' : 'Signing In...')
                            : (isSignup ? 'Create Account' : 'Sign In')
                        }
                    </Button>
                </form>

                <div className="mt-4 text-center">
                    <button
                        type="button"
                        onClick={() => {
                            setIsSignup(!isSignup)
                            resetForm()
                        }}
                        className="text-sm text-blue-600 hover:text-blue-800 underline"
                        disabled={isLoading}
                    >
                        {isSignup
                            ? 'Already have an account? Sign in'
                            : "Don't have an account? Sign up"
                        }
                    </button>
                </div>

                <div className="mt-4 text-center">
                    <p className="text-xs text-gray-500">
                        Demo Mode: Use any email/password to continue
                    </p>
                </div>
            </CardContent>
        </Card>
    )
}
