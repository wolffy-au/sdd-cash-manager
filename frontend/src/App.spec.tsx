import { render, screen } from '@testing-library/react';
import App from './App';

test('renders headers', () => {
  render(<App />);
  expect(screen.getByText('SDD Cash Manager UI Makeover')).toBeInTheDocument();
});
