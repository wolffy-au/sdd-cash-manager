import { test, expect } from '@playwright/test';

test('fetching unreconciled shows the discrepancy guidance panel', async ({ page }) => {
  await page.goto('http://127.0.0.1:4173');
  await page.getByRole('button', { name: 'Fetch Unreconciled' }).click();
  const insight = page.getByTestId('discrepancy-insight');
  await expect(insight).toBeVisible();
  await expect(insight).toContainText('Difference under target');
  await expect(page.getByRole('button', { name: 'Highlight UNCLEARED rows' })).toBeVisible();
});
