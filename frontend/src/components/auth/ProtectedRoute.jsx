import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import LoadingState from '../common/LoadingState';
import { useAuth } from '../../context/AuthContext';

export default function ProtectedRoute({ children, permission }) {
  const { loading, isAuthenticated, hasPermission } = useAuth();
  const location = useLocation();

  if (loading) return <LoadingState message="Checking session…" testId="auth-loading" />;

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (permission && !hasPermission(permission)) {
    return (
      <div className="p-8 text-center" data-testid="permission-denied">
        <h2 className="text-lg font-semibold">Permission Denied</h2>
        <p className="text-muted-foreground text-sm mt-2">You do not have access to this feature.</p>
      </div>
    );
  }

  return children;
}
