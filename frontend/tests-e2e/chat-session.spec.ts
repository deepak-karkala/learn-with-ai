import { test, expect } from '@playwright/test'

test('session persists for returning user', async ({ page, context }) => {
    // Start at chat page
    await page.goto('/chat')

    // Ensure storage is clear first
    await context.clearCookies()
    await context.clearPermissions()
    await page.evaluate(() => localStorage.clear())

    // Send first message – capture session id from network response and localStorage
    await page.getByTestId('message-input').fill('First visit message')
    await page.getByTestId('send-button').click()
    const firstResp = await page.waitForResponse(r => r.url().endsWith('/api/chat') && r.request().method() === 'POST', { timeout: 30000 })
    await expect(page.getByTestId('ai-response')).toBeVisible({ timeout: 20_000 })
    const firstJson = await firstResp.json()
    const sessionFromResponse1: string | undefined = firstJson?.session_id

    const initialSessionId = await page.evaluate(() => {
        // We know key format from app: sessionId:john@example.com
        return window.localStorage.getItem('sessionId:john@example.com')
    })
    expect(initialSessionId).toBeTruthy()
    expect(sessionFromResponse1).toBeTruthy()
    expect(initialSessionId).toBe(sessionFromResponse1)

    // Simulate user returning later: new page context
    const page2 = await context.newPage()
    await page2.goto('/chat')

    // LocalStorage should still contain session id
    const restoredSessionId = await page2.evaluate(() => {
        return window.localStorage.getItem('sessionId:john@example.com')
    })
    expect(restoredSessionId).toBe(initialSessionId)

    // Send another message; server should continue same session
    await page2.getByTestId('message-input').fill('Returning visit message')
    await page2.getByTestId('send-button').click()
    const secondResp = await page2.waitForResponse(r => r.url().endsWith('/api/chat') && r.request().method() === 'POST', { timeout: 30000 })
    await expect(page2.getByTestId('ai-response')).toHaveCount(2, { timeout: 20_000 }) // Should now have 2 responses
    const secondJson = await secondResp.json()
    const sessionFromResponse2: string | undefined = secondJson?.session_id

    const afterMessageSessionId = await page2.evaluate(() => {
        return window.localStorage.getItem('sessionId:john@example.com')
    })
    expect(afterMessageSessionId).toBe(initialSessionId)
    expect(sessionFromResponse2).toBe(initialSessionId)
})


