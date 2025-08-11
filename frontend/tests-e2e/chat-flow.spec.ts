import { test, expect } from '@playwright/test'

test('complete chat flow', async ({ page }) => {
    await page.goto('/chat')

    // Type message
    await page.getByTestId('message-input').fill('Hello, I want to learn system design')
    await page.getByTestId('send-button').click()

    // Wait for AI response to appear
    await expect(page.getByTestId('ai-response')).toBeVisible({ timeout: 20_000 })
})


