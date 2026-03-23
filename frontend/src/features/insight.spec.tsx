import { fireEvent, render, screen, within } from '@testing-library/react';
import ReconciliationFeature from './reconciliation';

test('discrepancy insight surfaces guidance and filters UNCLEARED rows', () => {
  render(<ReconciliationFeature />);
  fireEvent.click(screen.getByRole('button', { name: /Fetch Unreconciled/i }));

  const insight = screen.getByTestId('discrepancy-insight');
  expect(insight).toBeVisible();
  expect(within(insight).getByText(/Difference under target/i)).toBeInTheDocument();
  expect(within(insight).getByText(/Remaining: 3/)).toBeInTheDocument();

  const filter = screen.getByRole('button', { name: /Highlight UNCLEARED rows/i });
  fireEvent.click(filter);

  const selectedCheckboxes = screen.getAllByRole('checkbox').filter((checkbox) => checkbox.checked);
  expect(selectedCheckboxes).toHaveLength(3);
  expect(within(insight).getByText(/Remaining: 0/)).toBeInTheDocument();
});
