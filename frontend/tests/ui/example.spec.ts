import { test, expect } from '@playwright/test';

test('placeholder layout loads', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  await expect(page.getByText('SDD Cash Manager UI Makeover')).toBeVisible();
});
