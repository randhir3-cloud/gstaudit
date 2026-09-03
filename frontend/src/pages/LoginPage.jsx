import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import theme from '../theme/theme';
import { cn } from '../lib/utils';
import { DEFAULT_ROUTE } from '../config/appModules';

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!loading && isAuthenticated) {
    // Redirect to previously attempted route, or fall back to DEFAULT_ROUTE.
    // DEFAULT_ROUTE is /merge — the current active module.
    return <Navigate to={location.state?.from?.pathname || DEFAULT_ROUTE} replace />;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(username, password);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6" data-testid="login-page">
      <form onSubmit={handleSubmit} className={cn(theme.card.shell, 'w-full max-w-md p-8 space-y-6')}>
        <div>
          <h1 className={theme.text.heading}>GAIS Sign In</h1>
          <p className={theme.text.label}>GST Audit Intelligence System — Government Officer Login</p>
        </div>
        {error && <p className="text-sm text-destructive" data-testid="login-error">{error}</p>}
        <div className="space-y-2">
          <label htmlFor="username" className={theme.text.label}>Username</label>
          <Input id="username" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" data-testid="login-username" required />
        </div>
        <div className="space-y-2">
          <label htmlFor="password" className={theme.text.label}>Password</label>
          <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" data-testid="login-password" required />
        </div>
        <Button type="submit" className="w-full" disabled={submitting} data-testid="login-submit">
          {submitting ? 'Signing in…' : 'Sign In'}
        </Button>
      </form>
    </div>
  );
}
