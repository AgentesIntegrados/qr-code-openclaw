'use client'

import Header from './header';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Header />
      {children}
    </>
  );
}
