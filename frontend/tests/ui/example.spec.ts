import { test, expect } from '@playwright/test';

test('placeholder layout loads', async ({ page }) => {
  await page.goto('http://127.0.0.1:4173');
  await expect(page.getByText('SDD Cash Manager UI Makeover')).toBeVisible();
});
