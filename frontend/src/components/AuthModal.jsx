// import react hooks
import React, { useState } from 'react';
// import lucide icons
import { X, Lock, Mail, User, Shield, CheckCircle2, ArrowRight } from 'lucide-react';
// import api client
import { api } from '../services/api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  // tab state login register
  const [isLoginTab, setIsLoginTab] = useState(true);
  // form input fields
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    role: 'analyst'
  });
  // loading state
  const [isLoading, setIsLoading] = useState(false);
  // error state
  const [error, setError] = useState(null);

  if (!isOpen) return null; // hide if closed

  // handle input change
  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  // handle submit
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      let res;
      if (isLoginTab) {
        res = await api.login({
          email_or_username: formData.username || formData.email,
          password: formData.password
        });
      } else {
        res = await api.register({
          email: formData.email,
          username: formData.username,
          password: formData.password,
          full_name: formData.full_name,
          role: formData.role
        });
      }
      if (onAuthSuccess) onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  // quick demo credentials login
  const handleQuickDemo = async (username, password) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.login({ email_or_username: username, password });
      if (onAuthSuccess) onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setError(err.message || 'Demo login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    // modal overlay backdrop
    <div style={{ position: 'fixed', inset: 0, zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)' }}>
      {/* modal box container */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '16px', width: '100%', maxWidth: '440px', padding: '28px', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)', position: 'relative' }}>
        {/* close modal button */}
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '20px', right: '20px', background: 'transparent', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
        >
          <X size={20} />
        </button>

        {/* modal title header */}
        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>
            {isLoginTab ? 'Sign in to SalesPulse' : 'Create SalesPulse Account'}
          </h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '4px' }}>
            {isLoginTab ? 'Enter your credentials to access enterprise sales analytics' : 'Register to manage ETL pipelines and custom dashboards'}
          </p>
        </div>

        {/* quick demo buttons */}
        <div style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '20px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', display: 'block', marginBottom: '8px' }}>
            ONE-CLICK DEMO ACCOUNTS (PRE-SEEDED)
          </span>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={() => handleQuickDemo('admin', 'admin123')}
            >
              <Shield size={12} color="#0d9488" />
              <span>Admin</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={() => handleQuickDemo('analyst', 'analyst123')}
            >
              <User size={12} color="#2563eb" />
              <span>Analyst</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
              onClick={() => handleQuickDemo('viewer', 'viewer123')}
            >
              <Lock size={12} color="#64748b" />
              <span>Viewer</span>
            </button>
          </div>
        </div>

        {/* tabs switch */}
        <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', marginBottom: '20px' }}>
          <button
            type="button"
            onClick={() => { setIsLoginTab(true); setError(null); }}
            style={{ flex: 1, padding: '10px', background: 'none', border: 'none', borderBottom: isLoginTab ? '2px solid #0d9488' : 'none', fontWeight: isLoginTab ? 700 : 500, color: isLoginTab ? '#0d9488' : '#64748b', cursor: 'pointer' }}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsLoginTab(false); setError(null); }}
            style={{ flex: 1, padding: '10px', background: 'none', border: 'none', borderBottom: !isLoginTab ? '2px solid #0d9488' : 'none', fontWeight: !isLoginTab ? 700 : 500, color: !isLoginTab ? '#0d9488' : '#64748b', cursor: 'pointer' }}
          >
            Register
          </button>
        </div>

        {/* error feedback alert */}
        {error && (
          <div style={{ padding: '10px 14px', background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '6px', color: '#991b1b', fontSize: '0.8rem', marginBottom: '16px' }}>
            {error}
          </div>
        )}

        {/* auth input form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {!isLoginTab && (
            <div>
              <label className="filter-label">Full Name</label>
              <input
                type="text"
                name="full_name"
                className="text-input"
                style={{ width: '100%', marginTop: '4px' }}
                placeholder="Vallepu Revanth"
                value={formData.full_name}
                onChange={handleChange}
              />
            </div>
          )}

          {!isLoginTab && (
            <div>
              <label className="filter-label">Email Address *</label>
              <input
                type="email"
                name="email"
                className="text-input"
                style={{ width: '100%', marginTop: '4px' }}
                placeholder="revanth@example.com"
                required
                value={formData.email}
                onChange={handleChange}
              />
            </div>
          )}

          <div>
            <label className="filter-label">{isLoginTab ? 'Username or Email *' : 'Username *'}</label>
            <input
              type="text"
              name="username"
              className="text-input"
              style={{ width: '100%', marginTop: '4px' }}
              placeholder={isLoginTab ? 'admin or admin@salespulse.io' : 'revanth'}
              required
              value={formData.username}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="filter-label">Password *</label>
            <input
              type="password"
              name="password"
              className="text-input"
              style={{ width: '100%', marginTop: '4px' }}
              placeholder="••••••••"
              required
              value={formData.password}
              onChange={handleChange}
            />
          </div>

          {!isLoginTab && (
            <div>
              <label className="filter-label">Role Assignment *</label>
              <select
                name="role"
                className="select-input"
                style={{ width: '100%', marginTop: '4px' }}
                value={formData.role}
                onChange={handleChange}
              >
                <option value="analyst">Analyst (Upload, Run ETL, Explore)</option>
                <option value="admin">Admin (Full Access & User Control)</option>
                <option value="viewer">Viewer (Read-Only Analytics)</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '10px', padding: '11px' }}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <div className="spinner" style={{ width: '14px', height: '14px' }}></div>
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                <span>{isLoginTab ? 'Sign In' : 'Create Account'}</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
