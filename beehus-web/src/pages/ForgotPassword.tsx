import { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');
    setMessage('');
    try {
      await axios.post(`${apiBaseUrl}/users/request-password-reset`, { email });
      setMessage('If an account exists with this email, a password reset link has been sent.');
    } catch (err) {
      setError('Failed to request password reset.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg">
      <div className="w-full max-w-md p-8 glass rounded-2xl shadow-2xl border border-white/10 mx-4">
        <h1 className="text-2xl font-bold text-white mb-2">Forgot Password</h1>
        <p className="text-slate-400 mb-6">We will email you a reset link.</p>

        {message && <div className="p-3 rounded bg-green-500/20 text-green-300 text-sm mb-4">{message}</div>}
        {error && <div className="p-3 rounded bg-red-500/20 text-red-300 text-sm mb-4">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="w-full px-4 py-3 bg-dark-bg/50 border border-dark-border rounded-lg text-white"
            placeholder="Email"
            required
          />
          <button
            type="submit"
            className="w-full py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-semibold"
          >
            Send Reset Link
          </button>
        </form>

        <div className="mt-4 text-center">
          <Link to="/login" className="text-sm text-brand-400 hover:text-brand-300">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
}
