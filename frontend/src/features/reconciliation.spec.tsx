import { render, screen } from '@testing-library/react';
import ReconciliationFeature from './reconciliation';

test('renders reconciliation controls and discrepancy insight panel', () => {
  render(<ReconciliationFeature />);
  expect(screen.getByTestId('session-controls')).toBeInTheDocument();
  expect(screen.getByTestId('discrepancy-insight')).toBeInTheDocument();
  expect(screen.getByText(/Remaining:/)).toBeInTheDocument();
});
