import { render, screen } from '@testing-library/react';
import LedgerFeature from './ledger';

test('renders ledger feature with tree and register', () => {
  render(<LedgerFeature />);
  expect(screen.getByTestId('ledger-feature')).toBeInTheDocument();
  expect(screen.getByTestId('account-tree')).toBeInTheDocument();
  expect(screen.getByTestId('register')).toBeInTheDocument();
});
