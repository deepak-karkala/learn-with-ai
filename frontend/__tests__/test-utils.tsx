import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { ThemeProvider } from '@/contexts/ThemeContext'

// Mock localStorage for tests
const mockLocalStorage = {
  getItem: jest.fn(() => 'light'),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
})

// Mock matchMedia for theme detection
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ThemeProvider>
      {children}
    </ThemeProvider>
  )
}

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }