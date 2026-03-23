import { test, expect } from '@playwright/test';

test('fetching unreconciled updates badge', async ({ page }) => {
  await page.goto('http://127.0.0.1:4173');
  await page.getByRole('button', { name: 'Fetch Unreconciled' }).click();
  const badge = page.getByTestId('difference-badge');
  await expect(badge).toBeVisible();
  await expect(badge).toContainText('120.50');
});
