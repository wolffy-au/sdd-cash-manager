import { test, expect } from '@playwright/test';

test('ledger tree renders and selects account', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  const accountTree = page.getByTestId('account-tree');
  await expect(accountTree).toBeVisible();
  await page.getByText('Assets').click();
  await expect(page.getByText('checking', { exact: false })).toBeVisible();
});
