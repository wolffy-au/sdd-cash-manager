import { render, screen } from '@testing-library/react';
import App from './App';

test('renders app and hides reconciliation by default', () => {
  render(<App />);
  expect(screen.getByText('SDD Cash Manager')).toBeInTheDocument();
  expect(screen.queryByTestId('reconciliation-feature')).not.toBeInTheDocument();
});
