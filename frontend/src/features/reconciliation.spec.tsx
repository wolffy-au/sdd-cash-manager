import { render, screen } from '@testing-library/react';
import ReconciliationFeature from './reconciliation';

test('renders reconciliation controls and difference badge', () => {
  render(<ReconciliationFeature />);
  expect(screen.getByTestId('session-controls')).toBeInTheDocument();
  expect(screen.getByTestId('difference-badge')).toBeInTheDocument();
  expect(screen.getByText(/Difference:/)).toBeInTheDocument();
});
